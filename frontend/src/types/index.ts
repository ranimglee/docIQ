export type Status = 'UPLOADED'|'PROCESSING'|'COMPLETED'|'FAILED';
export interface Block { text:string; confidence:number; bbox:number[] }
export interface Document { id:number; filename:string; mime_type:string; file_size:number; page_count:number; document_type:string; status:Status; processing_time:number|null; error_message:string|null; created_at:string; ocr_results:{page_number:number;text:string;confidence:number;bounding_boxes:Block[]}[]; extracted_fields:{field_name:string;field_value:string|null;confidence:number}[] }
export interface DocumentPage {items:Document[];total:number;page:number;page_size:number}
export interface Value {value:string|number|null;confidence:number}
export interface Party {name:Value;address:Value;email:Value;phone:Value;tax_id:Value}
export interface LineItem {description:Value;quantity:Value;unit:Value;unit_price:Value;vat_rate:Value;amount:Value}
export interface InvoiceExtraction {invoice_number:Value;issue_date:Value;due_date:Value;currency:Value;supplier:Party;customer:Party;items:LineItem[];financials:Record<string,Value>;payment_information:Record<string,Value>;notes:Value[]}
export interface Validation {is_valid:boolean;checks:{name:string;status:'PASS'|'FAIL'|'WARNING'|'NOT_CHECKED';expected:number|null;actual:number|null;difference:number|null;message:string}[]}
export interface Review {status:'NOT_REVIEWED'|'REVIEWED';source:string}
export interface RichDocument extends Document {extraction:InvoiceExtraction|null;validation:Validation|null;review:Review|null}
