import axios from 'axios'; import type {Document,DocumentPage,InvoiceExtraction,RichDocument} from '../types';
const api=axios.create({baseURL:'/api'});
export const documentsApi={
 list:(params?:Record<string,string|number|undefined>)=>api.get<DocumentPage>('/documents',{params}).then(r=>r.data),
 get:(id:string)=>api.get<RichDocument>(`/documents/${id}`).then(r=>r.data),
 upload:(file:File,onProgress:(n:number)=>void)=>{const form=new FormData();form.append('file',file);return api.post<{id:number}>('/documents/upload',form,{onUploadProgress:e=>onProgress(Math.round(e.loaded*100/(e.total||1)))}).then(r=>r.data)},
 process:(id:number)=>api.post<Document>(`/documents/${id}/process`).then(r=>r.data), updateExtraction:(id:number,extraction:InvoiceExtraction)=>api.put<RichDocument>(`/documents/${id}/extraction`,{extraction}).then(r=>r.data), delete:(id:number)=>api.delete(`/documents/${id}`), file:(id:number)=>`/api/documents/${id}/file`
};
