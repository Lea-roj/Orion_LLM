import { Component, Input, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-sidebar',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './sidebar.html',
  styleUrls: ['./sidebar.css']
})
export class SidebarComponent {
  @Input() documents: any[] = [];
  @Output() documentSelected = new EventEmitter<number>();
  @Output() viewChanged = new EventEmitter<'ner' | 'visualization'>();
  @Input() activeView: 'ner' | 'visualization' = 'ner';

  selectView(view: 'ner' | 'visualization') {
    this.activeView = view;
    this.viewChanged.emit(view);
  }
}
