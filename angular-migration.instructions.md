---
applyTo: "**/*.ts,**/*.html,**/*.scss,**/*.css,**/angular.json,**/package.json,**/tsconfig.json"
---

# Angular Version-Adaptive Migration Skill

A reusable Copilot skill for executing Angular upgrades between any major versions (e.g., 12→21, 16→21, 19→21). This skill performs the full migration — dependency download, deprecated API detection, spec change validation, code refactoring, and build verification.

## IMPORTANT: This Is an Execution Workflow, Not Just a Reference

When the user asks to upgrade Angular, you MUST:
1. **Run commands** (npm install, ng update) — not just suggest them
2. **Scan the codebase** for deprecated APIs, removed interfaces, and breaking patterns
3. **Download dependencies** via npm/yarn — not just update package.json
4. **Validate the build** after every change
5. **Refactor code** that uses deprecated/removed APIs

---

## Step 1: Assessment (EXECUTE — Don't Skip)

Run these checks BEFORE any migration:

```bash
# 1. Detect current Angular version
node -e "const pkg = require('./package.json'); console.log('Angular:', pkg.dependencies['@angular/core']); console.log('TypeScript:', pkg.devDependencies['typescript']); console.log('RxJS:', pkg.dependencies['rxjs']); console.log('Zone.js:', pkg.dependencies['zone.js']);"

# 2. Detect package manager
ls package-lock.json 2>/dev/null && echo "npm" || (ls yarn.lock 2>/dev/null && echo "yarn" || echo "pnpm")

# 3. Detect builder
node -e "const ang = require('./angular.json'); const proj = Object.values(ang.projects)[0]; console.log('Builder:', proj.architect.build.builder);"

# 4. Count deprecated patterns (scan codebase)
echo "=== Deprecated API Scan ==="
echo "NgModules:"; grep -r "@NgModule" src/ --include="*.ts" -l | wc -l
echo "*ngIf usage:"; grep -r "\\*ngIf" src/ --include="*.html" -l | wc -l
echo "*ngFor usage:"; grep -r "\\*ngFor" src/ --include="*.html" -l | wc -l
echo "*ngSwitch usage:"; grep -r "\\*ngSwitch" src/ --include="*.html" -l | wc -l
echo "@Input() decorators:"; grep -r "@Input()" src/ --include="*.ts" -l | wc -l
echo "@Output() decorators:"; grep -r "@Output()" src/ --include="*.ts" -l | wc -l
echo "@ViewChild decorators:"; grep -r "@ViewChild" src/ --include="*.ts" -l | wc -l
echo "Class-based guards:"; grep -r "implements CanActivate\|implements CanDeactivate\|implements Resolve" src/ --include="*.ts" -l | wc -l
echo "HttpClientModule:"; grep -r "HttpClientModule" src/ --include="*.ts" -l | wc -l
echo "subscribe() calls:"; grep -r "\.subscribe(" src/ --include="*.ts" -l | wc -l

# 5. Check for deprecated RxJS patterns (v6 → v7 issues)
echo "=== RxJS Deprecation Scan ==="
echo "toPromise():"; grep -r "\.toPromise()" src/ --include="*.ts" | wc -l
echo "throwError(string):"; grep -rP "throwError\(['\"]" src/ --include="*.ts" | wc -l
echo "rxjs/internal imports:"; grep -r "from 'rxjs/internal" src/ --include="*.ts" | wc -l

# 6. Check third-party Angular dependencies
echo "=== Third-Party Dependencies ==="
node -e "const pkg = require('./package.json'); const deps = {...pkg.dependencies, ...pkg.devDependencies}; Object.entries(deps).filter(([k]) => k.includes('angular') || k.includes('ng-') || k.includes('ngx-') || k.includes('primeng') || k.includes('ngrx')).forEach(([k,v]) => console.log(k + ': ' + v));"
```

Output this as a **Migration Assessment Report** before proceeding.

---

## Step 2: Hop Execution (FULL WORKFLOW PER HOP)

### Hop Strategy — Never skip versions:
```
12 → 14 → 16 → 18 → 21
```

### Per-Hop Execution (COMPLETE — Not Just package.json)

For EACH hop from version X to version Y, execute ALL of the following:

#### 2.1 Update Angular CLI globally (required for ng update to work)

```bash
npm install -g @angular/cli@Y
```

#### 2.2 Run ng update (this downloads dependencies AND runs migration schematics)

```bash
# This does MORE than update package.json — it:
# - Updates package.json versions
# - Runs npm install (downloads all dependencies)
# - Executes built-in migration schematics (code transforms)
# - Updates angular.json if needed
ng update @angular/core@Y @angular/cli@Y

# If peer dependency errors occur:
ng update @angular/core@Y @angular/cli@Y --force
```

#### 2.3 Update TypeScript and other core dependencies (DOWNLOAD them)

```bash
# npm install actually DOWNLOADS the packages — not just edits package.json
npm install typescript@[required-version]
npm install rxjs@[required-version]
npm install zone.js@[required-version]

# Install all updated dependencies
npm install
```

#### 2.4 Update third-party dependencies to compatible versions

```bash
# Check what's outdated
npm outdated

# Update Angular Material (if used)
ng update @angular/material@Y @angular/cdk@Y

# Update other Angular-specific libraries
npm install [library]@[compatible-version]

# Reinstall everything cleanly if issues persist
rm -rf node_modules package-lock.json
npm install
```

#### 2.5 SCAN for deprecated APIs introduced in this hop

After updating, scan for code that uses APIs removed/deprecated in version Y:

```bash
# Per-hop deprecation scanning:

# === Hop to Angular 14 ===
# Check: FormGroup/FormControl without generics (typed forms introduced)
grep -rn "new FormGroup({" src/ --include="*.ts"
grep -rn "new FormControl(" src/ --include="*.ts"
# Check: @angular/flex-layout (deprecated)
grep -r "@angular/flex-layout" package.json

# === Hop to Angular 15/16 ===
# Check: Class-based guards (deprecated)
grep -rn "implements CanActivate" src/ --include="*.ts"
grep -rn "implements CanDeactivate" src/ --include="*.ts"
grep -rn "implements Resolve" src/ --include="*.ts"
# Check: RouterModule.forRoot patterns that need updating
grep -rn "RouterModule.forRoot" src/ --include="*.ts"

# === Hop to Angular 17/18 ===
# Check: Structural directives that should become control flow
grep -rn "\\*ngIf" src/ --include="*.html"
grep -rn "\\*ngFor" src/ --include="*.html"
# Check: HttpClientModule (should become provideHttpClient)
grep -rn "HttpClientModule" src/ --include="*.ts"
# Check: Old builder
grep -n "build-angular:browser" angular.json
# Check: ComponentModule patterns (should be standalone)
grep -rn "@NgModule" src/ --include="*.ts"

# === Hop to Angular 19/20/21 ===
# Check: @Input/@Output decorators (should become signals)
grep -rn "@Input(" src/ --include="*.ts"
grep -rn "@Output(" src/ --include="*.ts"
grep -rn "@ViewChild(" src/ --include="*.ts"
grep -rn "@ViewChildren(" src/ --include="*.ts"
grep -rn "@ContentChild(" src/ --include="*.ts"
# Check: Constructor injection (should become inject())
grep -rn "constructor(" src/ --include="*.ts" | grep -v "spec.ts"
```

#### 2.6 RUN migration schematics (these actually TRANSFORM the code)

```bash
# These are NOT just suggestions — they rewrite your source files:

# After reaching Angular 15+: Convert to standalone
ng generate @angular/core:standalone --mode convert-to-standalone --path src
ng generate @angular/core:standalone --mode prune-ng-modules --path src
ng generate @angular/core:standalone --mode standalone-bootstrap --path src

# After reaching Angular 17+: Migrate template syntax
ng generate @angular/core:control-flow --path src

# After reaching Angular 19+: Migrate to signals
ng generate @angular/core:signal-input-migration --path src
ng generate @angular/core:output-migration --path src
ng generate @angular/core:signal-queries-migration --path src
ng generate @angular/core:inject-migration --path src
```

#### 2.7 FIX remaining compilation errors

```bash
# Build and capture errors
ng build 2>&1 | tee build-output.log

# Common fixes needed (ACTUALLY refactor the code, don't just report):
```

**Fix: Class-based guards → Functional guards**
```typescript
// FIND this pattern:
@Injectable({ providedIn: 'root' })
export class AuthGuard implements CanActivate {
  constructor(private authService: AuthService, private router: Router) {}
  canActivate(route: ActivatedRouteSnapshot): boolean {
    if (this.authService.isAuthenticated()) return true;
    this.router.navigate(['/login']);
    return false;
  }
}

// REPLACE WITH:
export const authGuard: CanActivateFn = () => {
  const authService = inject(AuthService);
  const router = inject(Router);
  if (authService.isAuthenticated()) return true;
  return router.createUrlTree(['/login']);
};
```

**Fix: HttpClientModule → provideHttpClient()**
```typescript
// FIND in app.module.ts or any module:
imports: [HttpClientModule]

// REPLACE WITH (in app.config.ts):
providers: [provideHttpClient(withInterceptorsFromDi())]
```

**Fix: RxJS deprecated patterns**
```typescript
// FIND: toPromise() — REMOVED
const result = await this.http.get('/api/data').toPromise();
// REPLACE WITH:
const result = await firstValueFrom(this.http.get('/api/data'));

// FIND: throwError with string
throwError('Something went wrong');
// REPLACE WITH:
throwError(() => new Error('Something went wrong'));
```

**Fix: Old builder in angular.json**
```json
// FIND:
"builder": "@angular-devkit/build-angular:browser"
// REPLACE WITH:
"builder": "@angular-devkit/build-angular:application"
```

#### 2.8 VALIDATE (build + test + lint)

```bash
# ALL THREE must pass before proceeding to next hop:

# 1. Production build
ng build --configuration=production
echo "Build status: $?"

# 2. Run tests
ng test --watch=false --browsers=ChromeHeadless
echo "Test status: $?"

# 3. Lint
ng lint
echo "Lint status: $?"

# 4. Check for runtime deprecation warnings
ng serve &
sleep 10
# Check browser console for deprecation warnings
kill %1
```

**Do NOT proceed to the next hop until all three pass.**

#### 2.9 COMMIT the hop

```bash
git add -A
git commit -m "chore(angular): upgrade from v$X to v$Y

- Updated @angular/core, @angular/cli to v$Y
- Updated TypeScript to [version]
- Ran migration schematics: [list what ran]
- Fixed deprecated APIs: [list what was refactored]
- All tests passing, production build verified"
```

---

## Step 3: Post-Migration Verification

After ALL hops are complete:

```bash
# 1. Full clean rebuild
rm -rf node_modules dist .angular
npm install
ng build --configuration=production

# 2. Bundle size comparison
echo "Check bundle size:"
ls -la dist/*/browser/*.js | awk '{total += $5} END {print "Total bundle:", total/1024, "KB"}'

# 3. Run ALL tests
ng test --watch=false --code-coverage --browsers=ChromeHeadless

# 4. Check for remaining deprecated APIs (should be zero)
echo "=== Remaining Deprecated Patterns ==="
grep -r "\\*ngIf\|\\*ngFor\|\\*ngSwitch" src/ --include="*.html" | wc -l
grep -r "@Input()\|@Output()\|@ViewChild(" src/ --include="*.ts" | wc -l
grep -r "HttpClientModule" src/ --include="*.ts" | wc -l
grep -r "implements CanActivate\|implements Resolve" src/ --include="*.ts" | wc -l

# 5. Verify no leftover deprecated imports
grep -r "from '@angular/http'" src/ --include="*.ts"
grep -r "rxjs/internal" src/ --include="*.ts"
```

---

## Dependency Version Matrix (MUST match after each hop)

| Angular | TypeScript | RxJS | Zone.js | Node.js | npm install command |
|---------|-----------|------|---------|---------|---------------------|
| 14 | ~4.7 | ^7.5 | ~0.11.8 | 16+ | `npm i typescript@4.7 rxjs@7.5 zone.js@0.11.8` |
| 16 | ~5.0 | ^7.8 | ~0.13.0 | 18+ | `npm i typescript@5.0 rxjs@7.8 zone.js@0.13` |
| 18 | ~5.4 | ^7.8 | ~0.14.0 | 18.19+ | `npm i typescript@5.4 rxjs@7.8 zone.js@0.14` |
| 21 | ~5.7 | ^7.8 | ~0.15.0 | 20.11+ | `npm i typescript@5.7 rxjs@7.8 zone.js@0.15` |

**After updating package.json, ALWAYS run `npm install` to download the actual packages.**

---

## Quick Reference: What Each Schematic Actually DOES (Not Just "Runs")

| Schematic | What It Changes In Your Code |
|-----------|------------------------------|
| `ng update @angular/core@X` | Updates package.json + runs `npm install` + executes built-in code migrations |
| `@angular/core:standalone --mode convert-to-standalone` | Adds `standalone: true` to components, moves imports from NgModule into component |
| `@angular/core:standalone --mode prune-ng-modules` | Deletes NgModule files that are no longer needed |
| `@angular/core:standalone --mode standalone-bootstrap` | Replaces `platformBrowserDynamic().bootstrapModule(AppModule)` with `bootstrapApplication(AppComponent, appConfig)` |
| `@angular/core:control-flow` | Rewrites `*ngIf` → `@if`, `*ngFor` → `@for` (with track), `*ngSwitch` → `@switch` in all HTML templates |
| `@angular/core:signal-input-migration` | Converts `@Input() name: string` → `name = input<string>()` and updates templates to use `name()` |
| `@angular/core:output-migration` | Converts `@Output() clicked = new EventEmitter()` → `clicked = output()` |
| `@angular/core:signal-queries-migration` | Converts `@ViewChild('x') ref: ElementRef` → `ref = viewChild<ElementRef>('x')` |
| `@angular/core:inject-migration` | Converts `constructor(private svc: MyService)` → `private svc = inject(MyService)` |

---

## Troubleshooting (Execute Fixes, Don't Just Report)

### Problem: `npm install` fails with peer dependency errors
```bash
# Fix: Force install and resolve manually
npm install --legacy-peer-deps
# Then check what's actually incompatible:
npm ls @angular/core
# Update the conflicting package:
npm install [conflicting-package]@latest
```

### Problem: Build fails after ng update
```bash
# Get specific error details:
ng build 2>&1 | grep -A 2 "Error:"
# Common: Module not found → package was renamed or moved
# Common: Type error → TypeScript version stricter
# Common: Template error → Structural directive syntax changed
```

### Problem: Tests fail after migration
```bash
# Run tests with verbose output:
ng test --watch=false --browsers=ChromeHeadless 2>&1 | grep "FAILED\|Error"
# Common fix: TestBed.configureTestingModule needs standalone imports:
# Replace imports: [AppModule] with imports: [ComponentUnderTest] + providers
```

### Problem: node_modules corrupted after version jump
```bash
# Nuclear clean and reinstall:
rm -rf node_modules package-lock.json .angular
npm cache clean --force
npm install
ng build
```
