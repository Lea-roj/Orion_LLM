import {
  Component,
  ElementRef,
  Input,
  OnChanges,
  SimpleChanges,
  ViewChild
} from '@angular/core';

import { Network } from 'vis-network/standalone';

@Component({
  selector: 'app-graph',
  standalone: true,
  templateUrl: './graph.html',
  styleUrls: ['./graph.css']
})
export class GraphComponent implements OnChanges {

  @Input() graphData: any;
  @ViewChild('graphContainer', { static: true })
  container!: ElementRef<HTMLDivElement>;

  network?: Network;

  ngOnChanges(changes: SimpleChanges) {
    if (changes['graphData'] && this.graphData) {
      this.render();
    }
  }

  render() {
    const nodes = this.graphData.nodes.map((n: any) => ({
      id: n.id,
      label: n.label,
      shape: 'dot',
      size: 20,
      color: {
        background: '#715a5a',
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
  }
}
