export interface NodeData {
  id: string;
  data?: {
    type?: string;
    label?: string;
    external_id?: string;
    [key: string]: unknown;
  };
}

export interface EdgeData {
  id?: string;
  source: string;
  target: string;
  data?: {
    label?: string;
    relation_type?: string;
    edge_key?: string;
    [key: string]: unknown;
  };
}

export interface GraphData {
  nodes?: NodeData[];
  edges?: EdgeData[];
}
