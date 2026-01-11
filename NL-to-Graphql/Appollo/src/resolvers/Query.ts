import * as falkor from "./falkorSource";

// Energy Data Resolvers - Connected to FalkorDB
export const Query = {
  Query: {
    // Building queries
    async building(_parent: any, { id, name }: { id?: string; name?: string }) {
      return falkor.getBuilding(id, name);
    },

    async buildings() {
      return falkor.getBuildings();
    },

    // Floor queries
    async floors(_parent: any, { buildingId }: { buildingId?: string }) {
      return falkor.getFloors(buildingId);
    },

    // Zone queries
    async zones(_parent: any, { floorId, buildingId }: { floorId?: string; buildingId?: string }) {
      return falkor.getZones(floorId, buildingId);
    },

    // System queries
    async systems(_parent: any, { buildingId, systemType }: { buildingId?: string; systemType?: string }) {
      return falkor.getSystems(buildingId, systemType);
    },

    // Equipment queries
    async equipment(_parent: any, { systemId, equipmentType }: { systemId?: string; equipmentType?: string }) {
      return falkor.getEquipment(systemId, equipmentType);
    },

    // Sensor queries
    async sensors(_parent: any, { zoneId, equipmentId, sensorType }: { zoneId?: string; equipmentId?: string; sensorType?: string }) {
      return falkor.getSensors(zoneId, equipmentId, sensorType);
    },

    // Meter queries
    async meters(_parent: any, { buildingId }: { buildingId?: string }) {
      return falkor.getMeters(buildingId);
    },

    // Timeseries queries
    async timeseries(_parent: any, { sensorId }: { sensorId?: string }) {
      return falkor.getTimeseries(sensorId);
    },

    // Count queries
    async sensorCount(_parent: any, { sensorType }: { sensorType?: string }) {
      return falkor.getSensorCount(sensorType);
    },

    async equipmentCount(_parent: any, { equipmentType }: { equipmentType?: string }) {
      return falkor.getEquipmentCount(equipmentType);
    },
  },

  // Field resolvers for nested types
  Building: {
    async floors(parent: any) {
      return falkor.getFloorsForBuilding(parent.id);
    },
    async systems(parent: any) {
      return falkor.getSystemsForBuilding(parent.id);
    },
    async meters(parent: any) {
      return falkor.getMetersForBuilding(parent.id);
    },
  },

  Floor: {
    async zones(parent: any) {
      return falkor.getZones(parent.id);
    },
  },

  HVACZone: {
    async sensors(parent: any) {
      return falkor.getSensorsForParent(parent.id);
    },
    async fedBy(parent: any) {
      return falkor.getEquipmentFeedingZone(parent.id);
    },
  },

  System: {
    async equipment(parent: any) {
      return falkor.getEquipmentForSystem(parent.id);
    },
  },

  Equipment: {
    async sensors(parent: any) {
      return falkor.getSensorsForParent(parent.id);
    },
  },

  Meter: {
    async sensors(parent: any) {
      return falkor.getSensorsForParent(parent.id);
    },
  },
};
