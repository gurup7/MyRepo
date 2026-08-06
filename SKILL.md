# Angular 21 Unit Test Coverage Skill

## What This Skill Does

Generates unit tests for Angular 21 applications to achieve >80% code coverage. Supports the current Karma + Jasmine + Istanbul setup (existing projects) and the new Vitest default (new projects or post-migration).

## Important: Testing Framework Status in Angular 21

| Tool | Status | Notes |
|------|--------|-------|
| **Karma** | Deprecated but SUPPORTED | Use `"runner": "karma"` in angular.json. Works fine for existing projects. |
| **Jasmine** | Supported with Karma | Test syntax (describe/it/expect) remains the same |
| **Istanbul** | Supported via karma-coverage | Coverage reports + thresholds work normally |
| **Vitest** | NEW DEFAULT for new projects | Uses `@vitest/coverage-v8` for coverage |

**Decision:** If you already have Karma/Jasmine/Istanbul working — keep it. Focus on writing tests. Migrate to Vitest later.

## Primary Target

Angular 21 applications using:
- Standalone components (default in Angular 21)
- Signals and computed signals
- New control flow (`@if`, `@for`, `@switch`, `@empty`, `@let`)
- Angular 21 features: resource API, signal inputs, output functions, `inject()` pattern

## When to Activate

| Goal | Example Prompt |
|------|---------------|
| Improve test coverage | "Generate tests to reach 80% coverage" |
| Test a component | "Write unit tests for this component" |
| Test a service | "Generate tests for UserService with mocked HTTP" |
| Measure coverage | "How do I run coverage and enforce 80% threshold?" |
| Test signals | "How to test signals and computed signals?" |
| Test new control flow | "Write tests for @if and @for templates" |

## Phase 1: Measure Current Coverage

### With Karma/Istanbul (your current setup)

```bash
# Run tests with coverage
ng test --no-watch --code-coverage

# Coverage report generated in: coverage/<project-name>/index.html
```

**Enforce 80% threshold in `karma.conf.js`:**
```javascript
coverageReporter: {
  dir: require('path').join(__dirname, './coverage/<project-name>'),
  subdir: '.',
  reporters: [
    { type: 'html' },
    { type: 'text-summary' },
    { type: 'lcov' }
  ],
  check: {
    global: {
      statements: 80,
      branches: 80,
      functions: 80,
      lines: 80
    }
  }
}
```

### With Vitest (if migrated)

```bash
# Install coverage package
npm install @vitest/coverage-v8 --save-dev

# Run with coverage
ng test --coverage --no-watch
```

## Phase 2: Identify Coverage Gaps

After running coverage, the Istanbul HTML report (`coverage/index.html`) shows:
- **Red lines** — not executed (need tests)
- **Yellow lines** — partially covered (branches not fully tested)
- **Green lines** — fully covered

**Prioritize test generation:**
1. Components with business logic (calculations, state management)
2. Services with HTTP calls and data transformations
3. Guards, interceptors, resolvers
4. Pipes with transformation logic
5. Directives
6. Simple template-only components (lowest priority)

## Phase 3: Generate Tests

### Test Setup Structure (Karma/Jasmine)

```typescript
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { MyComponent } from './my.component';

describe('MyComponent', () => {
  let component: MyComponent;
  let fixture: ComponentFixture<MyComponent>;
  let compiled: HTMLElement;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [MyComponent] // Standalone component = imports, NOT declarations
    }).compileComponents();

    fixture = TestBed.createComponent(MyComponent);
    component = fixture.componentInstance;
    compiled = fixture.nativeElement as HTMLElement;
    fixture.detectChanges(); // Initial render
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
```

**Key difference in Angular 21:** Standalone components go in `imports`, not `declarations`.

---

### Pattern 1: Testing Signals

Angular 21 uses signals extensively. They're just functions:

```typescript
// Component
export class CounterComponent {
  count = signal(0);
  doubleCount = computed(() => this.count() * 2);

  increment() {
    this.count.update(c => c + 1);
  }
}

// Tests
describe('CounterComponent', () => {
  let component: CounterComponent;
  let fixture: ComponentFixture<CounterComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [CounterComponent]
    }).compileComponents();
    fixture = TestBed.createComponent(CounterComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should initialize count to 0', () => {
    expect(component.count()).toBe(0);
  });

  it('should increment count', () => {
    component.increment();
    expect(component.count()).toBe(1);
  });

  it('should compute doubleCount correctly', () => {
    component.count.set(5);
    expect(component.doubleCount()).toBe(10);
  });

  it('should update DOM after signal change', () => {
    component.count.set(3);
    fixture.detectChanges(); // REQUIRED for DOM updates
    const el = fixture.nativeElement.querySelector('[data-testid="count"]');
    expect(el.textContent).toContain('3');
  });
});
```

**Rule:** Call `fixture.detectChanges()` after signal changes when testing DOM. Not needed when testing component properties directly.

---

### Pattern 2: Testing Signal Inputs (Angular 21)

```typescript
// Component with signal input
export class GreetingComponent {
  name = input.required<string>();
  greeting = computed(() => `Hello, ${this.name()}!`);
}

// Tests
describe('GreetingComponent', () => {
  it('should display greeting with input name', () => {
    const fixture = TestBed.createComponent(GreetingComponent);
    // Set signal input using componentRef
    fixture.componentRef.setInput('name', 'World');
    fixture.detectChanges();

    expect(fixture.nativeElement.textContent).toContain('Hello, World!');
  });
});
```

---

### Pattern 3: Testing Services with HTTP

```typescript
import { TestBed } from '@angular/core/testing';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { provideHttpClient } from '@angular/common/http';
import { UserService } from './user.service';

describe('UserService', () => {
  let service: UserService;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        UserService
      ]
    });
    service = TestBed.inject(UserService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify(); // Ensure no outstanding requests
  });

  it('should fetch users', () => {
    const mockUsers = [{ id: 1, name: 'John' }];

    service.getUsers().subscribe(users => {
      expect(users).toEqual(mockUsers);
    });

    const req = httpMock.expectOne('/api/users');
    expect(req.request.method).toBe('GET');
    req.flush(mockUsers);
  });

  it('should handle HTTP error', () => {
    service.getUsers().subscribe({
      error: (err) => {
        expect(err.status).toBe(500);
      }
    });

    const req = httpMock.expectOne('/api/users');
    req.flush('Server Error', { status: 500, statusText: 'Internal Server Error' });
  });
});
```

**Note:** In Angular 21, use `provideHttpClient()` + `provideHttpClientTesting()` instead of deprecated `HttpClientTestingModule`.

---

### Pattern 4: Testing New Control Flow (@if, @for, @switch)

```typescript
// Template uses @if and @for
// @if (items().length > 0) {
//   @for (item of items(); track item.id) {
//     <li [attr.data-testid]="'item-' + item.id">{{ item.name }}</li>
//   } @empty {
//     <p data-testid="empty-state">No items</p>
//   }
// }

describe('ItemListComponent', () => {
  let component: ItemListComponent;
  let fixture: ComponentFixture<ItemListComponent>;
  let compiled: HTMLElement;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ItemListComponent]
    }).compileComponents();
    fixture = TestBed.createComponent(ItemListComponent);
    component = fixture.componentInstance;
    compiled = fixture.nativeElement;
    fixture.detectChanges();
  });

  it('should show empty state when no items', () => {
    component.items.set([]);
    fixture.detectChanges();
    const empty = compiled.querySelector('[data-testid="empty-state"]');
    expect(empty).toBeTruthy();
    expect(empty?.textContent).toContain('No items');
  });

  it('should render items with @for', () => {
    component.items.set([
      { id: 1, name: 'Item A' },
      { id: 2, name: 'Item B' }
    ]);
    fixture.detectChanges();
    const items = compiled.querySelectorAll('li');
    expect(items.length).toBe(2);
    expect(items[0].textContent).toContain('Item A');
  });

  it('should hide list when @if condition is false', () => {
    component.items.set([]);
    fixture.detectChanges();
    const list = compiled.querySelector('ul');
    expect(list).toBeNull();
  });
});
```

---

### Pattern 5: Testing Components with Dependencies (inject() pattern)

```typescript
// Component using inject()
export class DashboardComponent {
  private userService = inject(UserService);
  private router = inject(Router);
  users = signal<User[]>([]);

  loadUsers() {
    this.userService.getUsers().subscribe(u => this.users.set(u));
  }
}

// Tests
describe('DashboardComponent', () => {
  let component: DashboardComponent;
  let fixture: ComponentFixture<DashboardComponent>;
  let userServiceSpy: jasmine.SpyObj<UserService>;

  beforeEach(async () => {
    userServiceSpy = jasmine.createSpyObj('UserService', ['getUsers']);
    userServiceSpy.getUsers.and.returnValue(of([{ id: 1, name: 'John' }]));

    await TestBed.configureTestingModule({
      imports: [DashboardComponent],
      providers: [
        { provide: UserService, useValue: userServiceSpy }
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(DashboardComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should load users on loadUsers()', () => {
    component.loadUsers();
    expect(component.users().length).toBe(1);
    expect(component.users()[0].name).toBe('John');
  });

  it('should call service once', () => {
    component.loadUsers();
    expect(userServiceSpy.getUsers).toHaveBeenCalledTimes(1);
  });
});
```

---

### Pattern 6: Testing Router Navigation

```typescript
import { provideRouter } from '@angular/router';
import { Router } from '@angular/router';

describe('NavigationComponent', () => {
  let router: Router;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [NavigationComponent],
      providers: [provideRouter([
        { path: 'home', component: HomeComponent },
        { path: 'about', component: AboutComponent }
      ])]
    }).compileComponents();

    router = TestBed.inject(Router);
  });

  it('should navigate to home', async () => {
    const spy = spyOn(router, 'navigate');
    // trigger navigation
    component.goHome();
    expect(spy).toHaveBeenCalledWith(['/home']);
  });
});
```

**Note:** Use `provideRouter()` instead of deprecated `RouterTestingModule`.

---

### Pattern 7: Testing Pipes

```typescript
import { CurrencyFormatPipe } from './currency-format.pipe';

describe('CurrencyFormatPipe', () => {
  let pipe: CurrencyFormatPipe;

  beforeEach(() => {
    pipe = new CurrencyFormatPipe();
  });

  it('should format number as currency', () => {
    expect(pipe.transform(1234.56)).toBe('$1,234.56');
  });

  it('should handle zero', () => {
    expect(pipe.transform(0)).toBe('$0.00');
  });

  it('should handle null', () => {
    expect(pipe.transform(null)).toBe('');
  });

  it('should handle negative values', () => {
    expect(pipe.transform(-100)).toBe('-$100.00');
  });
});
```

---

### Pattern 8: Testing Guards

```typescript
import { TestBed } from '@angular/core/testing';
import { authGuard } from './auth.guard';
import { AuthService } from './auth.service';
import { Router } from '@angular/router';
import { ActivatedRouteSnapshot, RouterStateSnapshot } from '@angular/router';

describe('authGuard', () => {
  let authService: jasmine.SpyObj<AuthService>;
  let router: jasmine.SpyObj<Router>;

  beforeEach(() => {
    authService = jasmine.createSpyObj('AuthService', ['isAuthenticated']);
    router = jasmine.createSpyObj('Router', ['navigate']);

    TestBed.configureTestingModule({
      providers: [
        { provide: AuthService, useValue: authService },
        { provide: Router, useValue: router }
      ]
    });
  });

  it('should allow access when authenticated', () => {
    authService.isAuthenticated.and.returnValue(true);
    const result = TestBed.runInInjectionContext(() =>
      authGuard({} as ActivatedRouteSnapshot, {} as RouterStateSnapshot)
    );
    expect(result).toBe(true);
  });

  it('should redirect to login when not authenticated', () => {
    authService.isAuthenticated.and.returnValue(false);
    TestBed.runInInjectionContext(() =>
      authGuard({} as ActivatedRouteSnapshot, {} as RouterStateSnapshot)
    );
    expect(router.navigate).toHaveBeenCalledWith(['/login']);
  });
});
```

---

### Pattern 9: Testing Interceptors

```typescript
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { provideHttpClient, withInterceptors } from '@angular/common/http';
import { authInterceptor } from './auth.interceptor';

describe('authInterceptor', () => {
  let httpMock: HttpTestingController;
  let httpClient: HttpClient;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        provideHttpClient(withInterceptors([authInterceptor])),
        provideHttpClientTesting()
      ]
    });
    httpClient = TestBed.inject(HttpClient);
    httpMock = TestBed.inject(HttpTestingController);
  });

  it('should add Authorization header', () => {
    httpClient.get('/api/data').subscribe();
    const req = httpMock.expectOne('/api/data');
    expect(req.request.headers.has('Authorization')).toBeTrue();
    expect(req.request.headers.get('Authorization')).toContain('Bearer');
  });
});
```

---

## Phase 4: Coverage Strategy for 80%

### Priority Matrix

| Priority | Component Type | Typical Coverage Impact | Test Effort |
|----------|---------------|------------------------|-------------|
| 1 (High) | Services with logic | High (lots of branches) | Medium |
| 2 (High) | Components with signals/computed | High (state transitions) | Medium |
| 3 (Medium) | Guards & Interceptors | Medium (few lines, high value) | Low |
| 4 (Medium) | Pipes | Medium (pure functions) | Low |
| 5 (Low) | Template-only components | Low (just rendering) | Low |
| 6 (Low) | Models/interfaces | N/A (no logic) | None |

### Coverage Quick Wins

1. **Test all services first** — they're pure logic, easy to mock, high line count
2. **Pipes** — Pure functions, one test file covers entire pipe in minutes
3. **Guards** — Usually 10-20 lines, 2-3 tests cover 100%
4. **Component initialization** — `it('should create')` alone covers constructor + ngOnInit

### Common Missed Branches

- `if/else` in services — always test BOTH paths
- Error handlers in HTTP — test error responses, not just success
- `switch` cases — test EVERY case including default
- Ternary operators in templates — test both true and false
- `@if` blocks — test when condition is true AND false
- Optional chaining `?.` — test when object is null/undefined

## Angular 21 Deprecated APIs to Avoid in Tests

| Old (Deprecated) | New (Use This) |
|---|---|
| `HttpClientTestingModule` | `provideHttpClient()` + `provideHttpClientTesting()` |
| `RouterTestingModule` | `provideRouter([])` |
| `declarations: [Component]` | `imports: [Component]` (standalone) |
| `@Input() name: string` | `name = input<string>()` (signal input) |
| `@Output() clicked = new EventEmitter()` | `clicked = output<void>()` |
| `*ngIf`, `*ngFor` | `@if`, `@for` |
| `ngOnInit` for data loading | `resource()` or `rxResource()` |
| `fixture.componentInstance.name = 'x'` | `fixture.componentRef.setInput('name', 'x')` |

## Future: Migrating to Vitest (When Ready)

When the client is ready to migrate from Karma to Vitest:

1. The test syntax (describe/it/expect) is nearly identical — TestBed works the same
2. Main changes: import from `vitest` instead of relying on Jasmine globals
3. Coverage uses `@vitest/coverage-v8` instead of Istanbul
4. Angular CLI provides: `ng generate config vitest` for migration
5. Official guide: https://angular.dev/guide/testing/migrating-to-vitest

**Migration is NOT required for 80% coverage target.**

## Files

| File | Purpose |
|------|---------|
| `SKILL.md` | This file |
| `copilot-instructions.md` | System-level directives for Copilot |

## Usage

```
@workspace Generate unit tests for all untested components to reach 80% coverage
```

```
@workspace Write tests for UserService including HTTP mocking and error handling
```

```
@workspace Test the DashboardComponent which uses signals and computed values
```

```
@workspace How do I enforce 80% coverage threshold in karma.conf.js?
```

## Sources

- [Angular Testing Guide (official)](https://angular.dev/guide/testing)
- [Angular Karma Testing Guide (official)](https://angular.dev/guide/testing/karma)
- [Testing Angular 21 with Vitest (dev.to)](https://dev.to/olayeancarh/testing-angular-21-components-with-vitest-a-complete-guide-8l2)
