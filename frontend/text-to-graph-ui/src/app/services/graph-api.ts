import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface GraphResponse {
  nodes: {
    id: string;
    label: string;
    type?: string;
    source: string;
  }[];
  edges: {
    head: string;
    tail: string;
    type: string;
    confidence: number;
  }[];
}

@Injectable({
  providedIn: 'root'
})
export class GraphApiService {

  private readonly API_URL = 'http://localhost:8001/extract-graph';

  constructor(private http: HttpClient) {}

  extractGraph(text: string): Observable<GraphResponse> {
    return this.http.post<GraphResponse>(this.API_URL, { text });
  }

  getStatus(id: number) {
    return this.http.get(`http://localhost:8001/documents/${id}/status`);
  }

  uploadFile(formData: FormData) {
    return this.http.post('http://localhost:8001/extract-graph-from-file', formData);
  }

  getDocuments(): Observable<any[]> {
    return this.http.get<any[]>('http://localhost:8001/documents');
  }

  getDocument(id: number) {
    return this.http.get(`http://localhost:8001/documents/${id}`);
  }

  extractText(body: any) {
    return this.http.post('http://localhost:8001/extract-graph-from-text', body);
  }

  deleteDocument(id: number) {
    return this.http.delete(`http://localhost:8001/documents/${id}`);
  }
}
