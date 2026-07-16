export type DocumentType = "RG" | "CPF" | "CNPJ";

export interface Document {
  id?: number;
  _tempId?: string;
  document_type: DocumentType;
  document: string;
  isDeleted?: boolean;
}

export interface Owner {
  id: number;
  name: string;
}

export interface Renter {
  id: number;
  name: string;
  primary_contact: string;
  secondary_contact: string | null;
  email: string | null;
}

export type PropertyType = "HOUSE" | "COMMERCIAL";

export interface Address {
  id: number;
  street_name: string;
  number: string;
  complement: string | null;
  neighborhood: string;
  city: string;
  state: string;
  zip_code: string;
  type: PropertyType;
}

export type ContractStatus = "PENDING" | "ACTIVE" | "EXPIRED" | "CANCELLED";

export interface Contract {
  id: number;
  renter_id: number;
  address_id: number;
  start_date: string;
  end_date: string;
  monthly_revenue: string;
  deposit_value: string;
  deposit_months: number;
  payment_day: number;
  status: ContractStatus;
}
