import { GraphQLResolveInfo } from 'graphql';
import { DataSourceContext } from '../types/DataSourceContext';
export type Maybe<T> = T | null;
export type InputMaybe<T> = Maybe<T>;
export type Exact<T extends { [key: string]: unknown }> = { [K in keyof T]: T[K] };
export type MakeOptional<T, K extends keyof T> = Omit<T, K> & { [SubKey in K]?: Maybe<T[SubKey]> };
export type MakeMaybe<T, K extends keyof T> = Omit<T, K> & { [SubKey in K]: Maybe<T[SubKey]> };
export type MakeEmpty<T extends { [key: string]: unknown }, K extends keyof T> = { [_ in K]?: never };
export type Incremental<T> = T | { [P in keyof T]?: P extends ' $fragmentName' | '__typename' ? T[P] : never };
/** All built-in and custom scalars, mapped to their actual values */
export type Scalars = {
  ID: { input: string; output: string; }
  String: { input: string; output: string; }
  Boolean: { input: boolean; output: boolean; }
  Int: { input: number; output: number; }
  Float: { input: number; output: number; }
  _FieldSet: { input: any; output: any; }
};

export type Building = {
  __typename?: 'Building';
  address?: Maybe<Scalars['String']['output']>;
  areaSqm?: Maybe<Scalars['Float']['output']>;
  description?: Maybe<Scalars['String']['output']>;
  energyClass?: Maybe<Scalars['String']['output']>;
  floors: Array<Floor>;
  id: Scalars['ID']['output'];
  meters: Array<Meter>;
  name: Scalars['String']['output'];
  systems: Array<System>;
  yearBuilt?: Maybe<Scalars['Int']['output']>;
};

export type Equipment = {
  __typename?: 'Equipment';
  capacity?: Maybe<Scalars['Float']['output']>;
  capacityUnit?: Maybe<Scalars['String']['output']>;
  equipmentType: Scalars['String']['output'];
  id: Scalars['ID']['output'];
  manufacturer?: Maybe<Scalars['String']['output']>;
  model?: Maybe<Scalars['String']['output']>;
  name: Scalars['String']['output'];
  sensors: Array<Sensor>;
};

export type Floor = {
  __typename?: 'Floor';
  id: Scalars['ID']['output'];
  level?: Maybe<Scalars['Int']['output']>;
  name: Scalars['String']['output'];
  zones: Array<HvacZone>;
};

export type HvacZone = {
  __typename?: 'HVACZone';
  fedBy: Array<Equipment>;
  id: Scalars['ID']['output'];
  name: Scalars['String']['output'];
  sensors: Array<Sensor>;
};

export type Meter = {
  __typename?: 'Meter';
  id: Scalars['ID']['output'];
  meterType: Scalars['String']['output'];
  name: Scalars['String']['output'];
  sensors: Array<Sensor>;
  unit?: Maybe<Scalars['String']['output']>;
};

export type Query = {
  __typename?: 'Query';
  /** Get a building by ID or name */
  building?: Maybe<Building>;
  /** Get all buildings */
  buildings: Array<Building>;
  /** Get equipment (AHU, Chiller, Pump, etc.) */
  equipment: Array<Equipment>;
  /** Count equipment by type */
  equipmentCount: Scalars['Int']['output'];
  /** Get floors, optionally filtered by building */
  floors: Array<Floor>;
  /** Get meters for a building */
  meters: Array<Meter>;
  /** Count sensors by type */
  sensorCount: Scalars['Int']['output'];
  /** Get sensors with optional filters */
  sensors: Array<Sensor>;
  /** Get systems (HVAC, Electrical, Lighting) */
  systems: Array<System>;
  /** Get timeseries references */
  timeseries: Array<Timeseries>;
  /** Get HVAC zones */
  zones: Array<HvacZone>;
};


export type QueryBuildingArgs = {
  id?: InputMaybe<Scalars['ID']['input']>;
  name?: InputMaybe<Scalars['String']['input']>;
};


export type QueryEquipmentArgs = {
  equipmentType?: InputMaybe<Scalars['String']['input']>;
  systemId?: InputMaybe<Scalars['ID']['input']>;
};


export type QueryEquipmentCountArgs = {
  equipmentType?: InputMaybe<Scalars['String']['input']>;
};


export type QueryFloorsArgs = {
  buildingId?: InputMaybe<Scalars['ID']['input']>;
};


export type QueryMetersArgs = {
  buildingId?: InputMaybe<Scalars['ID']['input']>;
};


export type QuerySensorCountArgs = {
  sensorType?: InputMaybe<Scalars['String']['input']>;
};


export type QuerySensorsArgs = {
  equipmentId?: InputMaybe<Scalars['ID']['input']>;
  sensorType?: InputMaybe<Scalars['String']['input']>;
  zoneId?: InputMaybe<Scalars['ID']['input']>;
};


export type QuerySystemsArgs = {
  buildingId?: InputMaybe<Scalars['ID']['input']>;
  systemType?: InputMaybe<Scalars['String']['input']>;
};


export type QueryTimeseriesArgs = {
  sensorId?: InputMaybe<Scalars['ID']['input']>;
};


export type QueryZonesArgs = {
  buildingId?: InputMaybe<Scalars['ID']['input']>;
  floorId?: InputMaybe<Scalars['ID']['input']>;
};

export type Sensor = {
  __typename?: 'Sensor';
  id: Scalars['ID']['output'];
  name: Scalars['String']['output'];
  sensorType: Scalars['String']['output'];
  timeseries?: Maybe<Timeseries>;
  unit?: Maybe<Scalars['String']['output']>;
};

export type System = {
  __typename?: 'System';
  equipment: Array<Equipment>;
  id: Scalars['ID']['output'];
  name: Scalars['String']['output'];
  systemType: Scalars['String']['output'];
};

export type Timeseries = {
  __typename?: 'Timeseries';
  externalId: Scalars['String']['output'];
  id: Scalars['ID']['output'];
  resolution?: Maybe<Scalars['String']['output']>;
};

export type WithIndex<TObject> = TObject & Record<string, any>;
export type ResolversObject<TObject> = WithIndex<TObject>;

export type ResolverTypeWrapper<T> = Promise<T> | T;

export type ReferenceResolver<TResult, TReference, TContext> = (
      reference: TReference,
      context: TContext,
      info: GraphQLResolveInfo
    ) => Promise<TResult> | TResult;

      type ScalarCheck<T, S> = S extends true ? T : NullableCheck<T, S>;
      type NullableCheck<T, S> = Maybe<T> extends T ? Maybe<ListCheck<NonNullable<T>, S>> : ListCheck<T, S>;
      type ListCheck<T, S> = T extends (infer U)[] ? NullableCheck<U, S>[] : GraphQLRecursivePick<T, S>;
      export type GraphQLRecursivePick<T, S> = { [K in keyof T & keyof S]: ScalarCheck<T[K], S[K]> };
    

export type ResolverWithResolve<TResult, TParent, TContext, TArgs> = {
  resolve: ResolverFn<TResult, TParent, TContext, TArgs>;
};
export type Resolver<TResult, TParent = {}, TContext = {}, TArgs = {}> = ResolverFn<TResult, TParent, TContext, TArgs> | ResolverWithResolve<TResult, TParent, TContext, TArgs>;

export type ResolverFn<TResult, TParent, TContext, TArgs> = (
  parent: TParent,
  args: TArgs,
  context: TContext,
  info: GraphQLResolveInfo
) => Promise<TResult> | TResult;

export type SubscriptionSubscribeFn<TResult, TParent, TContext, TArgs> = (
  parent: TParent,
  args: TArgs,
  context: TContext,
  info: GraphQLResolveInfo
) => AsyncIterable<TResult> | Promise<AsyncIterable<TResult>>;

export type SubscriptionResolveFn<TResult, TParent, TContext, TArgs> = (
  parent: TParent,
  args: TArgs,
  context: TContext,
  info: GraphQLResolveInfo
) => TResult | Promise<TResult>;

export interface SubscriptionSubscriberObject<TResult, TKey extends string, TParent, TContext, TArgs> {
  subscribe: SubscriptionSubscribeFn<{ [key in TKey]: TResult }, TParent, TContext, TArgs>;
  resolve?: SubscriptionResolveFn<TResult, { [key in TKey]: TResult }, TContext, TArgs>;
}

export interface SubscriptionResolverObject<TResult, TParent, TContext, TArgs> {
  subscribe: SubscriptionSubscribeFn<any, TParent, TContext, TArgs>;
  resolve: SubscriptionResolveFn<TResult, any, TContext, TArgs>;
}

export type SubscriptionObject<TResult, TKey extends string, TParent, TContext, TArgs> =
  | SubscriptionSubscriberObject<TResult, TKey, TParent, TContext, TArgs>
  | SubscriptionResolverObject<TResult, TParent, TContext, TArgs>;

export type SubscriptionResolver<TResult, TKey extends string, TParent = {}, TContext = {}, TArgs = {}> =
  | ((...args: any[]) => SubscriptionObject<TResult, TKey, TParent, TContext, TArgs>)
  | SubscriptionObject<TResult, TKey, TParent, TContext, TArgs>;

export type TypeResolveFn<TTypes, TParent = {}, TContext = {}> = (
  parent: TParent,
  context: TContext,
  info: GraphQLResolveInfo
) => Maybe<TTypes> | Promise<Maybe<TTypes>>;

export type IsTypeOfResolverFn<T = {}, TContext = {}> = (obj: T, context: TContext, info: GraphQLResolveInfo) => boolean | Promise<boolean>;

export type NextResolverFn<T> = () => Promise<T>;

export type DirectiveResolverFn<TResult = {}, TParent = {}, TContext = {}, TArgs = {}> = (
  next: NextResolverFn<TResult>,
  parent: TParent,
  args: TArgs,
  context: TContext,
  info: GraphQLResolveInfo
) => TResult | Promise<TResult>;



/** Mapping between all available schema types and the resolvers types */
export type ResolversTypes = ResolversObject<{
  Building: ResolverTypeWrapper<Building>;
  String: ResolverTypeWrapper<Scalars['String']['output']>;
  Float: ResolverTypeWrapper<Scalars['Float']['output']>;
  ID: ResolverTypeWrapper<Scalars['ID']['output']>;
  Int: ResolverTypeWrapper<Scalars['Int']['output']>;
  Equipment: ResolverTypeWrapper<Equipment>;
  Floor: ResolverTypeWrapper<Floor>;
  HVACZone: ResolverTypeWrapper<HvacZone>;
  Meter: ResolverTypeWrapper<Meter>;
  Query: ResolverTypeWrapper<{}>;
  Sensor: ResolverTypeWrapper<Sensor>;
  System: ResolverTypeWrapper<System>;
  Timeseries: ResolverTypeWrapper<Timeseries>;
  Boolean: ResolverTypeWrapper<Scalars['Boolean']['output']>;
}>;

/** Mapping between all available schema types and the resolvers parents */
export type ResolversParentTypes = ResolversObject<{
  Building: Building;
  String: Scalars['String']['output'];
  Float: Scalars['Float']['output'];
  ID: Scalars['ID']['output'];
  Int: Scalars['Int']['output'];
  Equipment: Equipment;
  Floor: Floor;
  HVACZone: HvacZone;
  Meter: Meter;
  Query: {};
  Sensor: Sensor;
  System: System;
  Timeseries: Timeseries;
  Boolean: Scalars['Boolean']['output'];
}>;

export type BuildingResolvers<ContextType = DataSourceContext, ParentType extends ResolversParentTypes['Building'] = ResolversParentTypes['Building']> = ResolversObject<{
  __resolveReference?: ReferenceResolver<Maybe<ResolversTypes['Building']>, { __typename: 'Building' } & GraphQLRecursivePick<ParentType, {"id":true}>, ContextType>;
  address?: Resolver<Maybe<ResolversTypes['String']>, ParentType, ContextType>;
  areaSqm?: Resolver<Maybe<ResolversTypes['Float']>, ParentType, ContextType>;
  description?: Resolver<Maybe<ResolversTypes['String']>, ParentType, ContextType>;
  energyClass?: Resolver<Maybe<ResolversTypes['String']>, ParentType, ContextType>;
  floors?: Resolver<Array<ResolversTypes['Floor']>, ParentType, ContextType>;
  id?: Resolver<ResolversTypes['ID'], ParentType, ContextType>;
  meters?: Resolver<Array<ResolversTypes['Meter']>, ParentType, ContextType>;
  name?: Resolver<ResolversTypes['String'], ParentType, ContextType>;
  systems?: Resolver<Array<ResolversTypes['System']>, ParentType, ContextType>;
  yearBuilt?: Resolver<Maybe<ResolversTypes['Int']>, ParentType, ContextType>;
  __isTypeOf?: IsTypeOfResolverFn<ParentType, ContextType>;
}>;

export type EquipmentResolvers<ContextType = DataSourceContext, ParentType extends ResolversParentTypes['Equipment'] = ResolversParentTypes['Equipment']> = ResolversObject<{
  capacity?: Resolver<Maybe<ResolversTypes['Float']>, ParentType, ContextType>;
  capacityUnit?: Resolver<Maybe<ResolversTypes['String']>, ParentType, ContextType>;
  equipmentType?: Resolver<ResolversTypes['String'], ParentType, ContextType>;
  id?: Resolver<ResolversTypes['ID'], ParentType, ContextType>;
  manufacturer?: Resolver<Maybe<ResolversTypes['String']>, ParentType, ContextType>;
  model?: Resolver<Maybe<ResolversTypes['String']>, ParentType, ContextType>;
  name?: Resolver<ResolversTypes['String'], ParentType, ContextType>;
  sensors?: Resolver<Array<ResolversTypes['Sensor']>, ParentType, ContextType>;
  __isTypeOf?: IsTypeOfResolverFn<ParentType, ContextType>;
}>;

export type FloorResolvers<ContextType = DataSourceContext, ParentType extends ResolversParentTypes['Floor'] = ResolversParentTypes['Floor']> = ResolversObject<{
  id?: Resolver<ResolversTypes['ID'], ParentType, ContextType>;
  level?: Resolver<Maybe<ResolversTypes['Int']>, ParentType, ContextType>;
  name?: Resolver<ResolversTypes['String'], ParentType, ContextType>;
  zones?: Resolver<Array<ResolversTypes['HVACZone']>, ParentType, ContextType>;
  __isTypeOf?: IsTypeOfResolverFn<ParentType, ContextType>;
}>;

export type HvacZoneResolvers<ContextType = DataSourceContext, ParentType extends ResolversParentTypes['HVACZone'] = ResolversParentTypes['HVACZone']> = ResolversObject<{
  fedBy?: Resolver<Array<ResolversTypes['Equipment']>, ParentType, ContextType>;
  id?: Resolver<ResolversTypes['ID'], ParentType, ContextType>;
  name?: Resolver<ResolversTypes['String'], ParentType, ContextType>;
  sensors?: Resolver<Array<ResolversTypes['Sensor']>, ParentType, ContextType>;
  __isTypeOf?: IsTypeOfResolverFn<ParentType, ContextType>;
}>;

export type MeterResolvers<ContextType = DataSourceContext, ParentType extends ResolversParentTypes['Meter'] = ResolversParentTypes['Meter']> = ResolversObject<{
  id?: Resolver<ResolversTypes['ID'], ParentType, ContextType>;
  meterType?: Resolver<ResolversTypes['String'], ParentType, ContextType>;
  name?: Resolver<ResolversTypes['String'], ParentType, ContextType>;
  sensors?: Resolver<Array<ResolversTypes['Sensor']>, ParentType, ContextType>;
  unit?: Resolver<Maybe<ResolversTypes['String']>, ParentType, ContextType>;
  __isTypeOf?: IsTypeOfResolverFn<ParentType, ContextType>;
}>;

export type QueryResolvers<ContextType = DataSourceContext, ParentType extends ResolversParentTypes['Query'] = ResolversParentTypes['Query']> = ResolversObject<{
  building?: Resolver<Maybe<ResolversTypes['Building']>, ParentType, ContextType, Partial<QueryBuildingArgs>>;
  buildings?: Resolver<Array<ResolversTypes['Building']>, ParentType, ContextType>;
  equipment?: Resolver<Array<ResolversTypes['Equipment']>, ParentType, ContextType, Partial<QueryEquipmentArgs>>;
  equipmentCount?: Resolver<ResolversTypes['Int'], ParentType, ContextType, Partial<QueryEquipmentCountArgs>>;
  floors?: Resolver<Array<ResolversTypes['Floor']>, ParentType, ContextType, Partial<QueryFloorsArgs>>;
  meters?: Resolver<Array<ResolversTypes['Meter']>, ParentType, ContextType, Partial<QueryMetersArgs>>;
  sensorCount?: Resolver<ResolversTypes['Int'], ParentType, ContextType, Partial<QuerySensorCountArgs>>;
  sensors?: Resolver<Array<ResolversTypes['Sensor']>, ParentType, ContextType, Partial<QuerySensorsArgs>>;
  systems?: Resolver<Array<ResolversTypes['System']>, ParentType, ContextType, Partial<QuerySystemsArgs>>;
  timeseries?: Resolver<Array<ResolversTypes['Timeseries']>, ParentType, ContextType, Partial<QueryTimeseriesArgs>>;
  zones?: Resolver<Array<ResolversTypes['HVACZone']>, ParentType, ContextType, Partial<QueryZonesArgs>>;
}>;

export type SensorResolvers<ContextType = DataSourceContext, ParentType extends ResolversParentTypes['Sensor'] = ResolversParentTypes['Sensor']> = ResolversObject<{
  id?: Resolver<ResolversTypes['ID'], ParentType, ContextType>;
  name?: Resolver<ResolversTypes['String'], ParentType, ContextType>;
  sensorType?: Resolver<ResolversTypes['String'], ParentType, ContextType>;
  timeseries?: Resolver<Maybe<ResolversTypes['Timeseries']>, ParentType, ContextType>;
  unit?: Resolver<Maybe<ResolversTypes['String']>, ParentType, ContextType>;
  __isTypeOf?: IsTypeOfResolverFn<ParentType, ContextType>;
}>;

export type SystemResolvers<ContextType = DataSourceContext, ParentType extends ResolversParentTypes['System'] = ResolversParentTypes['System']> = ResolversObject<{
  equipment?: Resolver<Array<ResolversTypes['Equipment']>, ParentType, ContextType>;
  id?: Resolver<ResolversTypes['ID'], ParentType, ContextType>;
  name?: Resolver<ResolversTypes['String'], ParentType, ContextType>;
  systemType?: Resolver<ResolversTypes['String'], ParentType, ContextType>;
  __isTypeOf?: IsTypeOfResolverFn<ParentType, ContextType>;
}>;

export type TimeseriesResolvers<ContextType = DataSourceContext, ParentType extends ResolversParentTypes['Timeseries'] = ResolversParentTypes['Timeseries']> = ResolversObject<{
  externalId?: Resolver<ResolversTypes['String'], ParentType, ContextType>;
  id?: Resolver<ResolversTypes['ID'], ParentType, ContextType>;
  resolution?: Resolver<Maybe<ResolversTypes['String']>, ParentType, ContextType>;
  __isTypeOf?: IsTypeOfResolverFn<ParentType, ContextType>;
}>;

export type Resolvers<ContextType = DataSourceContext> = ResolversObject<{
  Building?: BuildingResolvers<ContextType>;
  Equipment?: EquipmentResolvers<ContextType>;
  Floor?: FloorResolvers<ContextType>;
  HVACZone?: HvacZoneResolvers<ContextType>;
  Meter?: MeterResolvers<ContextType>;
  Query?: QueryResolvers<ContextType>;
  Sensor?: SensorResolvers<ContextType>;
  System?: SystemResolvers<ContextType>;
  Timeseries?: TimeseriesResolvers<ContextType>;
}>;

