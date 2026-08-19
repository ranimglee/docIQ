import type {Block} from '../types';
export function OcrOverlay({blocks}:{blocks:Block[]}) { return <>{blocks.map((b,i)=><div key={i} className="ocr-box" title={`${b.text} (${Math.round(b.confidence*100)}%)`} style={{left:`${b.bbox[0]*100}%`,top:`${b.bbox[1]*100}%`,width:`${(b.bbox[2]-b.bbox[0])*100}%`,height:`${(b.bbox[3]-b.bbox[1])*100}%`}} />)}</> }
