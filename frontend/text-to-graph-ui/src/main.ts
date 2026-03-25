import { bootstrapApplication } from '@angular/platform-browser';
import { provideHttpClient } from '@angular/common/http';
import { AppComponent } from './app/app';
import 'zone.js';

bootstrapApplication(AppComponent, {
  providers: [provideHttpClient()]
});
