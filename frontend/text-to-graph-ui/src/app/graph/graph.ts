import {
  Component,
  ElementRef,
  Input,
  OnChanges,
  SimpleChanges,
  ViewChild
} from '@angular/core';

import { Network } from 'vis-network/standalone';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-graph',
  standalone: true,
  templateUrl: './graph.html',
  styleUrls: ['./graph.css'],
  imports: [CommonModule]
})
export class GraphComponent implements OnChanges {

  @Input() graphData: any;
  @ViewChild('graphContainer', { static: true })
  container!: ElementRef<HTMLDivElement>;

  network?: Network;
  selectedNode: any = null;

  ngOnChanges(changes: SimpleChanges) {
    if (changes['graphData'] && this.graphData) {
      this.render();
    }
  }

  getColor(type: string) {
    switch (type) {
      case 'PERSON': return '#4A90E2';
      case 'LOC': return '#50E3C2';
      case 'ORG': return '#F5A623';
      default: return '#715a5a';
    }
  }

  render() {
    const nodes = this.graphData.nodes.map((n: any) => ({
      id: n.id,
      label: n.label,
      shape: 'dot',
      size: 20,
      color: {
        background: this.getColor(n.type),
        border: '#D3DAD9'
      },
      font: {
        color: '#D3DAD9',
        size: 20
      }
    }));

    const edges = this.graphData.edges.map((e: any) => ({
      from: e.head,
      to: e.tail,
      label: e.type,
      arrows: 'to',
      font: {
        color: '#D3DAD9',
        strokeWidth: 0,
        size: 20
      }
    }));

    const data = { nodes, edges };

    const options = {
      physics: {
        barnesHut: {
          gravitationalConstant: -7000,   // more negative = more spread
          springLength: 200,              // longer edges = more spacing
          springConstant: 0.02
        },
        stabilization: true
      }
    };

    this.network = new Network(
      this.container.nativeElement,
      data,
      options
    );

    this.network.on('click', (params: any) => {
      if (params.nodes.length > 0) {
        const nodeId = params.nodes[0];

        this.selectedNode = this.graphData.nodes.find(
          (n: any) => n.id === nodeId
        );
      } else {
        this.selectedNode = null;
      }
    });
  }
}
