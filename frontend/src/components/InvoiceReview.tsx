import { useEffect, useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import type { InvoiceExtraction, RichDocument, Value } from "../types";
import { documentsApi } from "../services/api";

const humanize = (name: string) => name.replaceAll("_", " ");
const confidenceLabel = (field: Value) => field.confidence >= .9 ? "HIGH" : field.confidence >= .7 ? "MEDIUM" : "LOW";

function Field({ name, value, onChange }: { name: string; value: Value; onChange: (value: string) => void }) {
  return <label className="review-field"><span>{humanize(name)} <em>{Math.round(value.confidence * 100)}% · {confidenceLabel(value)}</em></span><input value={value.value ?? ""} onChange={event => onChange(event.target.value)} /></label>;
}

export function InvoiceReview({ document }: { document: RichDocument }) {
  const queryClient = useQueryClient();
  const [data, setData] = useState<InvoiceExtraction | null>(document.extraction);
  useEffect(() => setData(document.extraction), [document.extraction]);
  const save = useMutation({ mutationFn: (extraction: InvoiceExtraction) => documentsApi.updateExtraction(document.id, extraction), onSuccess: () => queryClient.invalidateQueries({ queryKey: ["document", String(document.id)] }) });
  if (!data) return null;
  const updateTop = (key: "invoice_number" | "issue_date" | "due_date" | "currency", value: string) => setData(current => current ? { ...current, [key]: { ...current[key], value } } : current);
  const updatePartyOrFinancial = (section: "supplier" | "customer" | "financials", key: string, value: string) => setData(current => current ? { ...current, [section]: { ...(current[section] as Record<string, Value>), [key]: { ...(current[section] as Record<string, Value>)[key], value } } } : current);
  const updateItem = (index: number, key: string, value: string) => setData(current => {
    if (!current) return current;
    const items = [...current.items];
    const item = { ...items[index], [key]: { ...(items[index] as unknown as Record<string, Value>)[key], value } } as typeof items[number];
    if (key === "quantity" || key === "unit_price") item.amount = { ...item.amount, value: (Number(item.quantity.value) || 0) * (Number(item.unit_price.value) || 0) };
    items[index] = item;
    return { ...current, items };
  });
  return <section className="card review"><div className="section-title"><div><h2>Invoice review</h2><p className="muted">{document.review?.status === "REVIEWED" ? "Reviewed correction" : "AI extracted — review before saving"}</p></div><button className="button" disabled={save.isPending} onClick={() => save.mutate(data)}>{save.isPending ? "Saving…" : "Save corrections"}</button></div><div className="review-grid">{(["invoice_number", "issue_date", "due_date", "currency"] as const).map(key => <Field key={key} name={key} value={data[key]} onChange={value => updateTop(key, value)} />)}</div><h3>Supplier</h3><div className="review-grid">{Object.entries(data.supplier).map(([key, value]) => <Field key={key} name={key} value={value} onChange={next => updatePartyOrFinancial("supplier", key, next)} />)}</div><h3>Customer</h3><div className="review-grid">{Object.entries(data.customer).map(([key, value]) => <Field key={key} name={key} value={value} onChange={next => updatePartyOrFinancial("customer", key, next)} />)}</div><h3>Line items</h3><div className="table-wrap"><table><thead><tr><th>Description</th><th>Qty</th><th>Unit</th><th>Price</th><th>VAT</th><th>Amount</th></tr></thead><tbody>{data.items.map((item, index) => <tr key={index}>{(["description", "quantity", "unit", "unit_price", "vat_rate", "amount"] as const).map(key => <td key={key}><input value={item[key].value ?? ""} onChange={event => updateItem(index, key, event.target.value)} /></td>)}</tr>)}</tbody></table></div><div className="review-grid">{Object.entries(data.financials).map(([key, value]) => <Field key={key} name={key} value={value} onChange={next => updatePartyOrFinancial("financials", key, next)} />)}</div>{save.isError && <p className="error">Could not save corrections.</p>}</section>;
}
