---
applyTo: "**/*.ts,**/*.html,**/*.scss,**/*.css,**/angular.json,**/package.json,**/tsconfig.json"
---

# Angular Version-Adaptive Migration Skill

A reusable Copilot skill for upgrading Angular applications between any major versions (e.g., 12→21, 16→21, 19→21). This skill is version-adaptive — it detects the current Angular version from package.json and applies only the patterns relevant to the hops needed.

## How to Use This Skill

1. Drop this file into your Angular project at `.github/instructions/angular-migration.instructions.md`
2. Open any `.ts`, `.html`, or Angular config file in your IDE
3. Ask Copilot Chat: "Upgrade this project from Angular [current] to [target]"
4. Copilot will follow the hop strategy and patterns defined below

## Assessment (First Step — Always Do This)

Before making any changes, assess the project:

1. Check `package.json` → `@angular/core` version (current version)
2. Check `angular.json` → builder type (webpack or esbuild)
3. Check if standalone components are already adopted (search for `standalone: true`)
4. Check if new control flow is already adopted (search for `@if` or `@for` in templates)
5. Compute hop plan: only apply hops between current version and target version

## Hop Strategy

Never skip major versions. The defined hop path is:

```
12 → 14 → 16 → 18 → 21
```

## Version-Specific Rules

### If currently on Angular 12-13:
- Do NOT use standalone components yet
- Do NOT use signals
- Do NOT use new control flow syntax
- Keep NgModule-based architecture
- Ensure RxJS 7 compatibility (replace deprecated operators)
- Use TypeScript 4.7

### If currently on Angular 14-15:
- Standalone components can be introduced (opt-in)
- Typed reactive forms are available — use `FormControl<T>`
- Migrate class-based route guards to functional guards
- Migrate class-based resolvers to functional resolvers
- Use TypeScript 5.0

### If currently on Angular 16-17:
- Use standalone components as default
- Run standalone migration schematic: `ng generate @angular/core:standalone`
- Run control flow migration: `ng generate @angular/core:control-flow`
- Replace `*ngIf` with `@if`, `*ngFor` with `@for`, `*ngSwitch` with `@switch`
- `@for` ALWAYS requires a `track` expression
- Migrate HttpClientModule to `provideHttpClient()`
- Switch to esbuild builder (`@angular-devkit/build-angular:application`)
- Use TypeScript 5.4

### If currently on Angular 18+:
- Use signal-based inputs: `input()` instead of `@Input()`
- Use signal-based outputs: `output()` instead of `@Output()`
- Use signal-based queries: `viewChild()`, `viewChildren()`, `contentChild()`, `contentChildren()`
- Signal inputs are accessed with `()` in templates: `{{ name() }}`
- Do NOT use `ngOnChanges` with signal inputs — use `effect()` instead
- Use `inject()` function instead of constructor injection
- Use `@defer` blocks for heavy components
- Use TypeScript 5.7

## Template Patterns

### Control Flow (Angular 17+)

```html
<!-- Conditional -->
@if (condition) {
  <div>Shown when true</div>
} @else {
  <div>Shown when false</div>
}

<!-- Loop — track is REQUIRED -->
@for (item of items; track item.id) {
  <div>{{ item.name }}</div>
} @empty {
  <div>No items</div>
}

<!-- Switch -->
@switch (status) {
  @case ('active') { <span>Active</span> }
  @case ('inactive') { <span>Inactive</span> }
  @default { <span>Unknown</span> }
}
```

### Signal Inputs/Outputs (Angular 18+)

```typescript
// Inputs
name = input<string>('');                    // optional with default
userId = input.required<string>();           // required
items = input<Item[]>([]);                   // with default array

// Outputs
clicked = output<string>();                  // replaces @Output() + EventEmitter
closed = output<void>();                     // void output

// Queries
chartRef = viewChild.required<ElementRef>('chart');
items = viewChildren(ItemComponent);
content = contentChild<TemplateRef<unknown>>('tmpl');
```

### Standalone Component (Angular 15+)

```typescript
import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';

@Component({
  selector: 'app-example',
  standalone: true,
  imports: [CommonModule, RouterModule],
  templateUrl: './example.component.html',
  styleUrl: './example.component.scss'
})
export class ExampleComponent {
  // Use inject() over constructor injection
  private readonly service = inject(MyService);
  private readonly router = inject(Router);
}
```

### Functional Guards (Angular 15+)

```typescript
// Do NOT use class-based guards
export const authGuard: CanActivateFn = (route, state) => {
  const authService = inject(AuthService);
  const router = inject(Router);

  if (authService.isAuthenticated()) {
    return true;
  }
  return router.createUrlTree(['/login']);
};
```

### Application Config (Angular 17+ standalone bootstrap)

```typescript
// app.config.ts
import { ApplicationConfig } from '@angular/core';
import { provideRouter } from '@angular/router';
import { provideHttpClient, withInterceptorsFromDi } from '@angular/common/http';

export const appConfig: ApplicationConfig = {
  providers: [
    provideRouter(routes),
    provideHttpClient(withInterceptorsFromDi()),
    provideAnimations(),
  ]
};
```

## ng update Commands Per Hop

```bash
# Hop 12→14
ng update @angular/core@14 @angular/cli@14
npm install typescript@4.7 rxjs@7

# Hop 14→16 (via 15)
ng update @angular/core@15 @angular/cli@15
ng update @angular/core@16 @angular/cli@16
npm install typescript@5.0

# Hop 16→18 (via 17)
ng update @angular/core@17 @angular/cli@17
ng update @angular/core@18 @angular/cli@18
npm install typescript@5.4

# Hop 18→21 (via 19, 20)
ng update @angular/core@19 @angular/cli@19
ng update @angular/core@20 @angular/cli@20
ng update @angular/core@21 @angular/cli@21
npm install typescript@5.7
```

## Built-in Migration Schematics

Run these AFTER reaching the appropriate version:

```bash
# Standalone migration (after reaching v15+)
ng generate @angular/core:standalone --mode convert-to-standalone
ng generate @angular/core:standalone --mode prune-ng-modules
ng generate @angular/core:standalone --mode standalone-bootstrap

# Control flow migration (after reaching v17+)
ng generate @angular/core:control-flow

# Signal inputs migration (after reaching v19+)
ng generate @angular/core:signal-input-migration

# Signal outputs migration (after reaching v19+)
ng generate @angular/core:output-migration

# Signal queries migration (after reaching v19+)
ng generate @angular/core:signal-queries-migration

# Inject function migration (after reaching v19+)
ng generate @angular/core:inject-migration
```

## Common Pitfalls

1. **@for without track** — Always add `track item.id` or `track $index`
2. **Signal inputs in templates** — Must use `{{ value() }}` not `{{ value }}`
3. **ngOnChanges with signals** — Does not work; use `effect()` instead
4. **CommonModule removed incorrectly** — Components using `ngTemplateOutlet`, `AsyncPipe`, or `DatePipe` still need explicit imports
5. **Peer dependency conflicts** — Use `ng update --force` when safe, or `npm install --legacy-peer-deps` as last resort
6. **esbuild vs Webpack** — Custom Webpack plugins won't work with the new `application` builder

## Validation After Each Hop

Always run after completing a hop:

```bash
ng build --configuration=production
ng test --watch=false --browsers=ChromeHeadless
ng lint
```

Do NOT proceed to the next hop until the build passes.

## Dependency Version Matrix

| Angular | TypeScript | RxJS | Zone.js | Node.js |
|---------|-----------|------|---------|---------|
| 12 | 4.2-4.3 | 6.x or 7.x | 0.11.x | 14+ |
| 14 | 4.6-4.8 | 7.5+ | 0.11.8 | 14.15+ or 16.10+ |
| 16 | 4.9-5.1 | 7.8+ | 0.13.x | 16.14+ or 18.10+ |
| 18 | 5.2-5.5 | 7.8+ | 0.14.x | 18.19+ or 20.11+ |
| 21 | 5.5-5.7 | 7.8+ | 0.15.x | 20.11+ or 22+ |

## Troubleshooting

### Peer dependency conflicts
```bash
ng update @angular/core@[version] @angular/cli@[version] --force
```

### Standalone migration removes CommonModule incorrectly
Re-import specific items the component needs:
```typescript
import { NgTemplateOutlet, AsyncPipe, DatePipe } from '@angular/common';
@Component({ standalone: true, imports: [NgTemplateOutlet, AsyncPipe, DatePipe] })
```

### @for migration — trackBy to track
```html
<!-- Before: *ngFor with trackBy function -->
<div *ngFor="let item of items; trackBy: trackById">

<!-- After: @for with inline track expression -->
@for (item of items; track item.id) {
  <div>{{ item.name }}</div>
}
```

### Signal input access in templates
```html
<!-- WRONG — shows [object Signal] -->
{{ userName }}

<!-- CORRECT — call the signal -->
{{ userName() }}
```

### OnChanges doesn't work with signal inputs
```typescript
// WRONG — ngOnChanges won't fire for signal inputs
ngOnChanges(changes: SimpleChanges) { ... }

// CORRECT — use effect()
constructor() {
  effect(() => {
    console.log('userId changed:', this.userId());
  });
}
```
