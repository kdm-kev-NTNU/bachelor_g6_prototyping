/**
 * FalkorDB Data Source for Energy Data
 * Connects to FalkorDB and executes Cypher queries
 */

import { createClient } from "redis";

const FALKOR_HOST = process.env.FALKORDB_HOST || "localhost";
const FALKOR_PORT = process.env.FALKORDB_PORT || "6379";
const GRAPH_NAME = process.env.FALKORDB_GRAPH || "energy_graph";

let client: ReturnType<typeof createClient> | null = null;

async function getClient() {
    if (!client) {
        client = createClient({
            url: `redis://${FALKOR_HOST}:${FALKOR_PORT}`,
        });
        await client.connect();
        console.log(`[FalkorDB] Connected to ${FALKOR_HOST}:${FALKOR_PORT}`);
    }
    return client;
}

function extractProps(node: any): Record<string, any> {
    if (!node) return {};
    if (node.properties) return node.properties;
    return node;
}

export async function query(cypher: string): Promise<any[]> {
    const redis = await getClient();
    try {
        const result = await redis.graph.query(GRAPH_NAME, cypher);

        if (!result.data || result.data.length === 0) {
            return [];
        }

        // Convert result to array of objects
        const headers = result.headers || [];
        return result.data.map((row: any[]) => {
            const obj: Record<string, any> = {};
            headers.forEach((header: string, i: number) => {
                obj[header] = extractProps(row[i]);
            });
            return obj;
        });
    } catch (error) {
        console.error("[FalkorDB] Query error:", error);
        return [];
    }
}

// Building queries
export async function getBuilding(id?: string, name?: string) {
    let where = "";
    if (id) where = `WHERE b.id = '${id}'`;
    else if (name) where = `WHERE b.name CONTAINS '${name}'`;

    const results = await query(`
    MATCH (b:brick_Building)
    ${where}
    RETURN b
    LIMIT 1
  `);

    return results[0]?.b || null;
}

export async function getBuildings() {
    const results = await query(`
    MATCH (b:brick_Building)
    RETURN b
  `);
    return results.map((r) => r.b);
}

// Floor queries
export async function getFloors(buildingId?: string) {
    if (buildingId) {
        const results = await query(`
      MATCH (b:brick_Building {id: '${buildingId}'})-[:brick_hasPart]->(f:brick_Floor)
      RETURN f
      ORDER BY f.level
    `);
        return results.map((r) => r.f);
    }

    const results = await query(`MATCH (f:brick_Floor) RETURN f ORDER BY f.level`);
    return results.map((r) => r.f);
}

export async function getFloorsForBuilding(buildingId: string) {
    return getFloors(buildingId);
}

// Zone queries
export async function getZones(floorId?: string, buildingId?: string) {
    if (floorId) {
        const results = await query(`
      MATCH (f:brick_Floor {id: '${floorId}'})-[:brick_hasPart]->(z:brick_HVAC_Zone)
      RETURN z
    `);
        return results.map((r) => r.z);
    }

    if (buildingId) {
        const results = await query(`
      MATCH (b:brick_Building {id: '${buildingId}'})-[:brick_hasPart]->(:brick_Floor)
            -[:brick_hasPart]->(z:brick_HVAC_Zone)
      RETURN z
    `);
        return results.map((r) => r.z);
    }

    const results = await query(`MATCH (z:brick_HVAC_Zone) RETURN z`);
    return results.map((r) => r.z);
}

// System queries
export async function getSystems(buildingId?: string, systemType?: string) {
    if (buildingId) {
        const results = await query(`
      MATCH (b:brick_Building {id: '${buildingId}'})-[:brick_hasPart]->(sys)
      WHERE NOT sys:brick_Floor
      RETURN sys, labels(sys)[0] as type
    `);
        return results.map((r) => ({ ...r.sys, systemType: r.type?.replace("brick_", "") }));
    }

    const results = await query(`
    MATCH (sys)
    WHERE sys:brick_HVAC_System OR sys:brick_Electrical_System OR sys:brick_Lighting_System
    RETURN sys, labels(sys)[0] as type
  `);
    return results.map((r) => ({ ...r.sys, systemType: r.type?.replace("brick_", "") }));
}

export async function getSystemsForBuilding(buildingId: string) {
    return getSystems(buildingId);
}

// Equipment queries
export async function getEquipment(systemId?: string, equipmentType?: string) {
    if (systemId) {
        const results = await query(`
      MATCH (sys {id: '${systemId}'})-[:brick_hasMember]->(eq)
      RETURN eq, labels(eq)[0] as type
    `);
        return results.map((r) => ({ ...r.eq, equipmentType: r.type?.replace("brick_", "") }));
    }

    const results = await query(`
    MATCH (eq)
    WHERE eq:brick_Air_Handling_Unit OR eq:brick_Chiller OR eq:brick_Pump OR eq:brick_Boiler
    RETURN eq, labels(eq)[0] as type
  `);
    return results.map((r) => ({ ...r.eq, equipmentType: r.type?.replace("brick_", "") }));
}

export async function getEquipmentForSystem(systemId: string) {
    return getEquipment(systemId);
}

export async function getEquipmentFeedingZone(zoneId: string) {
    const results = await query(`
    MATCH (eq)-[:brick_feeds]->(z:brick_HVAC_Zone {id: '${zoneId}'})
    RETURN eq, labels(eq)[0] as type
  `);
    return results.map((r) => ({ ...r.eq, equipmentType: r.type?.replace("brick_", "") }));
}

// Sensor queries
export async function getSensors(zoneId?: string, equipmentId?: string, sensorType?: string) {
    let match = "MATCH (s)";
    let where = "WHERE s:brick_Temperature_Sensor OR s:brick_Power_Sensor OR s:brick_CO2_Sensor OR s:brick_Energy_Sensor";

    if (zoneId) {
        match = `MATCH (z:brick_HVAC_Zone {id: '${zoneId}'})-[:brick_hasPoint]->(s)`;
        where = "";
    } else if (equipmentId) {
        match = `MATCH (eq {id: '${equipmentId}'})-[:brick_hasPoint]->(s)`;
        where = "";
    }

    const results = await query(`
    ${match}
    ${where}
    OPTIONAL MATCH (s)-[:brick_hasTimeseries]->(ts)
    RETURN s, labels(s)[0] as type, ts
  `);

    return results.map((r) => ({
        ...r.s,
        sensorType: r.type?.replace("brick_", ""),
        timeseries: r.ts || null,
    }));
}

export async function getSensorsForParent(parentId: string) {
    const results = await query(`
    MATCH (p {id: '${parentId}'})-[:brick_hasPoint]->(s)
    OPTIONAL MATCH (s)-[:brick_hasTimeseries]->(ts)
    RETURN s, labels(s)[0] as type, ts
  `);

    return results.map((r) => ({
        ...r.s,
        sensorType: r.type?.replace("brick_", ""),
        timeseries: r.ts || null,
    }));
}

// Meter queries
export async function getMeters(buildingId?: string) {
    if (buildingId) {
        const results = await query(`
      MATCH (b:brick_Building {id: '${buildingId}'})-[:brick_isMeteredBy]->(m)
      RETURN m, labels(m)[0] as type
    `);
        return results.map((r) => ({ ...r.m, meterType: r.type?.replace("brick_", "") }));
    }

    const results = await query(`
    MATCH (m)
    WHERE m:brick_Electrical_Meter OR m:brick_Thermal_Energy_Meter OR m:brick_Water_Meter
    RETURN m, labels(m)[0] as type
  `);
    return results.map((r) => ({ ...r.m, meterType: r.type?.replace("brick_", "") }));
}

export async function getMetersForBuilding(buildingId: string) {
    return getMeters(buildingId);
}

// Timeseries queries
export async function getTimeseries(sensorId?: string) {
    if (sensorId) {
        const results = await query(`
      MATCH (s {id: '${sensorId}'})-[:brick_hasTimeseries]->(ts:brick_Timeseries)
      RETURN ts
    `);
        return results.map((r) => r.ts);
    }

    const results = await query(`MATCH (ts:brick_Timeseries) RETURN ts`);
    return results.map((r) => r.ts);
}

// Count queries
export async function getSensorCount(sensorType?: string) {
    if (sensorType) {
        const results = await query(`MATCH (s:brick_${sensorType}) RETURN count(s) as count`);
        return results[0]?.count || 0;
    }

    const results = await query(`
    MATCH (s)
    WHERE s:brick_Temperature_Sensor OR s:brick_Power_Sensor OR s:brick_CO2_Sensor
    RETURN count(s) as count
  `);
    return results[0]?.count || 0;
}

export async function getEquipmentCount(equipmentType?: string) {
    if (equipmentType) {
        const results = await query(`MATCH (eq:brick_${equipmentType}) RETURN count(eq) as count`);
        return results[0]?.count || 0;
    }

    const results = await query(`
    MATCH (eq)
    WHERE eq:brick_Air_Handling_Unit OR eq:brick_Chiller OR eq:brick_Pump
    RETURN count(eq) as count
  `);
    return results[0]?.count || 0;
}
