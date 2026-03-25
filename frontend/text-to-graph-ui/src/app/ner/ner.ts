import {Component, Input, Output, EventEmitter, OnInit} from '@angular/core';
import { MatFormFieldModule } from '@angular/material/form-field';
import { CommonModule, JsonPipe } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { GraphApiService } from '../services/graph-api';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatTableModule } from '@angular/material/table';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatInputModule } from '@angular/material/input';
import {MatToolbarModule} from '@angular/material/toolbar';
import {MatIconModule} from '@angular/material/icon';
import { MatTooltipModule } from '@angular/material/tooltip';

@Component({
  selector: 'app-ner',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,

    MatButtonModule,
    MatCardModule,
    MatTableModule,
    MatProgressSpinnerModule,
    MatFormFieldModule,
    MatInputModule,
    MatToolbarModule,
    MatIconModule,
    MatTooltipModule
  ],
  templateUrl: './ner.html',
  styleUrls: ['./ner.css']
})
export class NerComponent implements OnInit {
  text = '';
  loading = false;
  selectedFile: File | null = null;
  graph: any = null;
  fileName = '';
  documents: any[] = [];
  status: 'idle' | 'translating' | 'learning' | 'done' = 'idle';

  constructor(private api: GraphApiService) {}

  @Output() graphLoaded = new EventEmitter<any>();

  ngOnInit() {
    this.api.getDocuments().subscribe((res: any) => {
      console.log('API documents:', res);

      this.documents = res.sort((a: any, b: any) => b.id - a.id);

      console.log('Sorted documents:', this.documents);

      this.documents.forEach(doc => {
        if (doc.status !== 'DONE') {
          this.pollStatus(doc.id);
        }
      });
    });
  }

  extract() {
    if (!this.text.trim()) return;

    const formData = { text: this.text };

    this.api.extractText(formData).subscribe((res: any) => {
      const docId = res.id;

      if (!this.documents.some(d => d.id === docId)) {
        this.documents = [
          {
            id: docId,
            filename: 'pasted_text',
            status: 'TRANSLATING',
            translated_pdf: null,
            created_at: new Date().toISOString()
          },
          ...this.documents
        ];
      }

      this.pollStatus(docId);
    });
  }

  onFileSelected(event: any) {
    this.selectedFile = event.target.files[0];
  }

  extractFromFile() {
    if (!this.selectedFile) return;

    this.fileName = this.selectedFile.name;
    this.status = 'translating';

    const formData = new FormData();
    formData.append('file', this.selectedFile);

    this.api.uploadFile(formData).subscribe({
      next: (res: any) => {
        const docId = res.id;

        if (!this.documents.some(d => d.id === docId)) {
          this.documents = [
            {
              id: docId,
              filename: this.fileName,
              status: 'TRANSLATING',
              translated_pdf: null,
              created_at: new Date().toISOString()
            },
            ...this.documents
          ];
        }

        this.pollStatus(docId);
      },
      error: () => {
        this.status = 'idle';
        alert('Error');
      }
    });
  }

  pollStatus(id: number) {
    let lastStatus = '';

    const interval = setInterval(() => {
      this.api.getStatus(id).subscribe((res: any) => {

        const doc = this.documents.find(d => d.id === id);

        if (res.status !== lastStatus) {
          lastStatus = res.status;

          if (doc) {
            doc.status = res.status;

            if (res.translated_pdf) {
              doc.translated_pdf = res.translated_pdf;
            }
          }
        }

        if (res.status === 'DONE') {
          clearInterval(interval);
        }
      });
    }, 1000);
  }

  loadGraph(id: number) {
    this.api.getDocument(id).subscribe((res: any) => {
      this.graphLoaded.emit(res);
    });
  }

  deleteDoc(id: number) {
    this.api.deleteDocument(id).subscribe(() => {
      this.documents = this.documents.filter(d => d.id !== id);
    });
  }

  trackById(index: number, doc: any) {
    return doc.id;
  }

  handleExtract() {
    if (this.loading) return;

    if (this.selectedFile) {
      this.extractFromFile();
    } else if (this.text.trim()) {
      this.extract();
    }
  }
}
