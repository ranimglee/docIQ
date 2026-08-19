import {useQuery} from '@tanstack/react-query';
import {Link,useParams} from 'react-router-dom';
import {documentsApi} from '../services/api';
import {Badge} from '../components/Badge';
import {OcrOverlay} from '../components/OcrOverlay';
import {InvoiceReview} from '../components/InvoiceReview';

export function DocumentDetails(){
 const {id=''}=useParams(); const {data:d,isLoading}=useQuery({queryKey:['document',id],queryFn:()=>documentsApi.get(id)});
 if(isLoading)return <main><p>Loading document…</p></main>; if(!d)return <main><p>Document not found.</p></main>;
 const blocks=d.ocr_results[0]?.bounding_boxes||[];
 const summaryFields: Array<[string,{value:string|number|null;confidence:number}]>=d.extraction?[["Invoice number",d.extraction.invoice_number],["Issue date",d.extraction.issue_date],["Due date",d.extraction.due_date],["Currency",d.extraction.currency],["Supplier",d.extraction.supplier.name],["Customer",d.extraction.customer.name]]:[];
 return <main><Link className="back" to="/documents">← All documents</Link><div className="heading"><div><p className="eyebrow">DOCUMENT #{d.id}</p><h1>{d.filename}</h1><Badge>{d.status}</Badge></div>{d.validation&&<span className={`validation-status ${d.validation.is_valid?'pass':'fail'}`}>{d.validation.is_valid?'✓ Internally consistent':'⚠ Needs review'}</span>}</div>{d.error_message&&<p className="error">{d.error_message}</p>}
 <section className="details"><article className="card preview"><h2>Document preview</h2><div className="canvas">{d.mime_type==='application/pdf'?<iframe title="Document preview" src={documentsApi.file(d.id)}/>:<><img src={documentsApi.file(d.id)} alt={d.filename}/><OcrOverlay blocks={blocks}/></>}</div><p className="muted">Hover highlighted regions to inspect OCR detections.</p></article><article className="card"><h2>Extracted information</h2><div className="type"><span>Document type</span><strong>{d.document_type.replace('_',' ')}</strong></div>{d.extraction? <>{summaryFields.map(([name,v])=><div className="field" key={name}><span>{name}</span><strong>{v.value||'Not detected'}</strong><small>{Math.round(v.confidence*100)}% confidence · {v.confidence>=.9?'HIGH':v.confidence>=.7?'MEDIUM':'LOW'}</small></div>)}</>:d.extracted_fields.map(f=><div className="field" key={f.field_name}><span>{f.field_name.replaceAll('_',' ')}</span><strong>{f.field_value||'Not detected'}</strong><small>{Math.round(f.confidence*100)}% confidence</small></div>)}</article></section>
 {d.extraction&&<><InvoiceReview document={d}/><section className="card validation"><h2>Document validation</h2>{d.validation?.checks.map(check=><div className="check" key={check.name}><strong>{check.status==='PASS'?'✓':check.status==='NOT_CHECKED'?'—':'⚠'} {check.message}</strong><span>{check.status}{check.difference!==null?` · difference ${check.difference.toFixed(2)}`:''}</span></div>)}</section></>}
 <section className="card ocr"><h2>OCR text</h2>{d.ocr_results.map(page=><div key={page.page_number}><h3>Page {page.page_number} <small>{Math.round(page.confidence*100)}% average confidence</small></h3><pre>{page.text||'No text detected.'}</pre></div>)}</section></main>
}
