import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatTableModule } from '@angular/material/table';

export interface RelationRow {
  head: string;
  type: string;
  tail: string;
  confidence: number;
}

@Component({
  selector: 'app-table',
  standalone: true,
  imports: [CommonModule, MatTableModule],
  templateUrl: './table.html',
  styleUrls: ['./table.scss']
})
export class TableComponent {
  @Input() relations: RelationRow[] = [];

  displayedColumns = ['from', 'type', 'to', 'confidence'];
}
