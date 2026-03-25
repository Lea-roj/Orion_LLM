import { Component } from '@angular/core';
import { CommonModule, JsonPipe } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { GraphApiService } from './services/graph-api';
import { Network, DataSet } from 'vis-network/standalone';
import type { Node, Edge } from 'vis-network';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatTableModule } from '@angular/material/table';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import {MatToolbarModule} from '@angular/material/toolbar';
import {MatIconModule} from '@angular/material/icon';
import { MatTooltipModule } from '@angular/material/tooltip';
import {TableComponent} from './table/table';
import {SidebarComponent} from './sidebar/sidebar';
import { OnInit } from '@angular/core';
import { NerComponent } from './ner/ner';
import {GraphComponent} from './graph/graph';

@Component({
  selector: 'app-root',
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
    MatTooltipModule,

    SidebarComponent,
    NerComponent,
    GraphComponent
  ],
  templateUrl: './app.html',
  styleUrls: ['./app.css']
})


export class AppComponent implements OnInit {
  text = '';
  loading = false;
  selectedFile: File | null = null;
  graph: any = null;
  selectedNode: any = null;
  fileName = '';
  translatedPdf = '';
  documents: any[] = [];
  status: 'idle' | 'translating' | 'learning' | 'done' = 'idle';
  currentView: 'ner' | 'visualization' = 'ner';

  constructor(private api: GraphApiService) {}

  ngOnInit() {
  this.api.getDocuments().subscribe((res: any) => {
    this.documents = res;
  });
}

  extract() {
    if (!this.text.trim()) return;

    this.loading = true;
    this.graph = null;
    this.selectedNode = null;

    this.api.extractGraph(this.text).subscribe({
      next: (res) => {
        this.graph = res;
        this.loading = false;

        setTimeout(() => this.renderGraph(), 0);
      },
      error: () => {
        this.loading = false;
        alert('Backend error');
      }
    });
  }

  renderGraph() {
    if (!this.graph) return;

    const nodes = new DataSet<Node>(
      this.graph.nodes.map((n: any): Node => ({
        id: n.id,
        label: n.label,
        color:
          n.type === 'PERSON'
            ? '#60a5fa'
            : n.type === 'ORG'
            ? '#34d399'
            : '#fbbf24',
        font: { color: '#111827' }
      }))
    );

    const edges = new DataSet<Edge>(
      this.graph.edges.map((e: any): Edge => ({
        from: e.head,
        to: e.tail,
        label: e.type,
        width: 1 + e.confidence * 4,
        arrows: 'to',
        color: { color: '#9ca3af' }
      }))
    );

    const container = document.getElementById('graphContainer');
    if (!container) return;

    const network = new Network(
      container,
      { nodes, edges },
      {
        interaction: {
          hover: true,
          zoomView: true,
          dragNodes: true
        },
        physics: {
          stabilization: false,
          barnesHut: {
            gravitationalConstant: -30000,
            springLength: 120
          }
        }
      }
    );

    network.on('click', params => {
      if (params.nodes.length) {
        const id = params.nodes[0];
        this.selectedNode = this.graph.nodes.find((n: any) => n.id === id);
      }
    });
  }


  loadDocument(id: number) {
    this.api.getDocument(id).subscribe((res: any) => {
      this.graph = res;

      this.fileName = res.filename;
      this.translatedPdf = res.translated_pdf;

      this.status = 'done';

      setTimeout(() => this.renderGraph(), 0);
    });
  }

  onGraphLoaded(graph: any) {
    this.graph = graph;
    this.currentView = 'visualization';
  }
}
