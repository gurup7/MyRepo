---
name: springboot-upgrade
description: 'Guide for migrating Spring Boot 2.x to Spring Boot 3.x (3.2/3.3/3.5) and Spring Framework 5.x to 6.x. Use when upgrading Spring Boot version, migrating javax to jakarta namespace, updating Spring Security configuration from WebSecurityConfigurerAdapter, fixing deprecated Spring MVC adapters, migrating application.properties keys, upgrading Hibernate 5 to 6, or resolving Spring Boot 3 compilation errors. Covers Spring Data, Spring Cloud, Actuator, and enterprise integration patterns.'
---

# Spring Boot 2.x to 3.x Upgrade

This skill provides comprehensive guidance for migrating enterprise Spring Boot applications from version 2.x (Spring Framework 5.x) to Spring Boot 3.x (Spring Framework 6.x), covering the javax→jakarta namespace migration, Spring Security rewrite, property key changes, Hibernate 6 upgrade, and enterprise integration patterns.

## When to Use This Skill

- Upgrading Spring Boot from 2.x to 3.x (any 3.x target: 3.2, 3.3, 3.5)
- Migrating `javax.*` imports to `jakarta.*` across the codebase
- Rewriting Spring Security configuration (removing `WebSecurityConfigurerAdapter`)
- Fixing `application.properties` / `application.yml` key deprecations
- Upgrading Hibernate from 5.x to 6.x
- Updating Spring Cloud dependencies to 2023.x / 2024.x train
- Resolving Actuator endpoint path changes
- Migrating Spring Data repositories with new query method behavior

## Prerequisites

- Java 17 or later (Spring Boot 3.x minimum requirement)
- Maven 3.8+ or Gradle 7.6+
- Complete Java 8→17 migration first (see `java-version-upgrade` skill)
- Application currently on Spring Boot 2.7.x (recommended intermediate step)

## Recommended Migration Path

Spring official recommendation is a **two-phase approach**:

```
Phase A: Upgrade to Spring Boot 2.7.x (latest patch)
         - Enables deprecation warnings for 3.x removals
         - Allows using spring-boot-properties-migrator

Phase B: Upgrade to Spring Boot 3.x
         - All javax → jakarta changes
         - Spring Security 6.x API
         - Hibernate 6.x
         - New property keys
```

If currently on Spring Boot 2.5 or earlier, do NOT jump directly to 3.x.

## Phase 1: Prepare on Spring Boot 2.7

### Add Properties Migrator (Temporary)

```xml
<!-- Add temporarily to detect deprecated properties -->
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-properties-migrator</artifactId>
    <scope>runtime</scope>
</dependency>
```

This logs warnings for every property key that changed in 3.x. Fix all warnings before upgrading.

### Enable Deprecation Warnings

```xml
<plugin>
    <groupId>org.apache.maven.plugins</groupId>
    <artifactId>maven-compiler-plugin</artifactId>
    <configuration>
        <compilerArgs>
            <arg>-Xlint:deprecation</arg>
        </compilerArgs>
    </configuration>
</plugin>
```

## Phase 2: javax to jakarta Namespace Migration

This is the single largest change. Every `javax.*` package in Java EE is now `jakarta.*`.

### Affected Packages

| Old (javax) | New (jakarta) | Common Usage |
|-------------|---------------|--------------|
| `javax.servlet.*` | `jakarta.servlet.*` | Filters, HttpServletRequest/Response |
| `javax.persistence.*` | `jakarta.persistence.*` | JPA entities, @Entity, @Column |
| `javax.validation.*` | `jakarta.validation.*` | Bean validation, @NotNull, @Valid |
| `javax.annotation.*` | `jakarta.annotation.*` | @PostConstruct, @PreDestroy, @Resource |
| `javax.transaction.*` | `jakarta.transaction.*` | @Transactional (JTA) |
| `javax.websocket.*` | `jakarta.websocket.*` | WebSocket endpoints |
| `javax.mail.*` | `jakarta.mail.*` | JavaMail / Email |
| `javax.inject.*` | `jakarta.inject.*` | CDI @Inject, @Named |
| `javax.enterprise.*` | `jakarta.enterprise.*` | CDI events, interceptors |

### Automated Find-and-Replace

For most projects, a bulk rename handles 90%+ of cases:

```bash
# Linux/Mac — find and replace in all Java files
find . -name "*.java" -exec sed -i 's/javax\.persistence/jakarta.persistence/g' {} +
find . -name "*.java" -exec sed -i 's/javax\.servlet/jakarta.servlet/g' {} +
find . -name "*.java" -exec sed -i 's/javax\.validation/jakarta.validation/g' {} +
find . -name "*.java" -exec sed -i 's/javax\.annotation/jakarta.annotation/g' {} +
find . -name "*.java" -exec sed -i 's/javax\.transaction/jakarta.transaction/g' {} +
find . -name "*.java" -exec sed -i 's/javax\.websocket/jakarta.websocket/g' {} +
find . -name "*.java" -exec sed -i 's/javax\.mail/jakarta.mail/g' {} +
```

### Packages That Do NOT Change

These stay as `javax.*` — do NOT rename:

| Package | Reason |
|---------|--------|
| `javax.sql.*` | Part of Java SE (not Java EE) |
| `javax.crypto.*` | Part of Java SE |
| `javax.net.*` | Part of Java SE |
| `javax.security.auth.*` | Part of Java SE |
| `javax.naming.*` | Part of Java SE (JNDI) |
| `javax.xml.parsers.*` | Part of Java SE |
| `javax.swing.*` | Part of Java SE |

### Maven Dependency Changes

```xml
<!-- Before (Spring Boot 2.x) -->
<dependency>
    <groupId>javax.persistence</groupId>
    <artifactId>javax.persistence-api</artifactId>
</dependency>
<dependency>
    <groupId>javax.validation</groupId>
    <artifactId>validation-api</artifactId>
</dependency>
<dependency>
    <groupId>javax.servlet</groupId>
    <artifactId>javax.servlet-api</artifactId>
</dependency>

<!-- After (Spring Boot 3.x) — managed by spring-boot-starter-parent -->
<dependency>
    <groupId>jakarta.persistence</groupId>
    <artifactId>jakarta.persistence-api</artifactId>
</dependency>
<dependency>
    <groupId>jakarta.validation</groupId>
    <artifactId>jakarta.validation-api</artifactId>
</dependency>
<dependency>
    <groupId>jakarta.servlet</groupId>
    <artifactId>jakarta.servlet-api</artifactId>
</dependency>
```

## Phase 3: Spring Boot 3.x POM Upgrade

### Parent POM

```xml
<parent>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-parent</artifactId>
    <version>3.3.6</version>
    <relativePath/>
</parent>
```

### Key Dependency Version Alignment

| Component | Spring Boot 2.7 | Spring Boot 3.3 |
|-----------|-----------------|-----------------|
| Spring Framework | 5.3.x | 6.1.x |
| Hibernate | 5.6.x | 6.4.x |
| Spring Security | 5.8.x | 6.3.x |
| Spring Data | 2.7.x | 3.3.x |
| Tomcat (embedded) | 9.0.x | 10.1.x |
| Jackson | 2.14.x | 2.17.x |
| Micrometer | 1.9.x | 1.13.x |
| Jakarta EE | 8 (javax) | 10 (jakarta) |

## Phase 4: Spring Security Migration

The most significant API change. `WebSecurityConfigurerAdapter` was removed entirely.

### Before (Spring Boot 2.x)

```java
@Configuration
@EnableWebSecurity
public class SecurityConfig extends WebSecurityConfigurerAdapter {

    @Override
    protected void configure(HttpSecurity http) throws Exception {
        http
            .authorizeRequests()
                .antMatchers("/api/public/**").permitAll()
                .antMatchers("/api/admin/**").hasRole("ADMIN")
                .anyRequest().authenticated()
            .and()
            .httpBasic();
    }

    @Override
    protected void configure(AuthenticationManagerBuilder auth) throws Exception {
        auth.ldapAuthentication()
            .userDnPatterns("uid={0},ou=people")
            .contextSource()
            .url("ldap://localhost:389/dc=example,dc=com");
    }
}
```

### After (Spring Boot 3.x)

```java
@Configuration
@EnableWebSecurity
public class SecurityConfig {

    @Bean
    public SecurityFilterChain securityFilterChain(HttpSecurity http) throws Exception {
        http
            .authorizeHttpRequests(auth -> auth
                .requestMatchers("/api/public/**").permitAll()
                .requestMatchers("/api/admin/**").hasRole("ADMIN")
                .anyRequest().authenticated()
            )
            .httpBasic(Customizer.withDefaults());
        return http.build();
    }

    @Bean
    public AuthenticationManager authenticationManager(
            AuthenticationConfiguration authConfig) throws Exception {
        return authConfig.getAuthenticationManager();
    }
}
```

### Key Spring Security API Changes

| Old API (Security 5.x) | New API (Security 6.x) |
|-------------------------|------------------------|
| `WebSecurityConfigurerAdapter` | `SecurityFilterChain` bean |
| `.authorizeRequests()` | `.authorizeHttpRequests()` |
| `.antMatchers()` | `.requestMatchers()` |
| `.mvcMatchers()` | `.requestMatchers()` |
| `.regexMatchers()` | `.requestMatchers(RegexRequestMatcher)` |
| `.access("hasRole('X')")` | `.access(AuthorizationManagers.hasRole("X"))` |
| `@EnableGlobalMethodSecurity` | `@EnableMethodSecurity` |
| `@Secured` | Still works with `@EnableMethodSecurity(securedEnabled=true)` |

### CSRF Configuration

```java
// Spring Boot 3.x — CSRF token now uses deferred loading
http.csrf(csrf -> csrf
    .csrfTokenRepository(CookieCsrfTokenRepository.withHttpOnlyFalse())
    .csrfTokenRequestHandler(new CsrfTokenRequestAttributeHandler())
);

// For REST APIs that need CSRF disabled:
http.csrf(csrf -> csrf.disable());
```

## Phase 5: Application Properties Migration

### Changed Property Keys

| Old Key (2.x) | New Key (3.x) |
|----------------|---------------|
| `spring.redis.*` | `spring.data.redis.*` |
| `spring.elasticsearch.*` | `spring.elasticsearch.uris` (restructured) |
| `spring.datasource.initialization-mode` | `spring.sql.init.mode` |
| `spring.datasource.schema` | `spring.sql.init.schema-locations` |
| `spring.datasource.data` | `spring.sql.init.data-locations` |
| `spring.jpa.defer-datasource-initialization` | `spring.jpa.defer-datasource-initialization` (unchanged) |
| `server.max-http-header-size` | `server.max-http-request-header-size` |
| `spring.mvc.throw-exception-if-no-handler-found` | Removed (now always true) |
| `spring.resources.add-mappings=false` | `spring.web.resources.add-mappings=false` |
| `management.metrics.export.*` | `management.<product>.metrics.export.*` |
| `spring.activemq.*` | `spring.jms.activemq.*` (some restructured) |

### Actuator Endpoint Changes

```yaml
# Spring Boot 2.x
management:
  endpoints:
    web:
      base-path: /actuator
  endpoint:
    health:
      show-details: always

# Spring Boot 3.x — same structure but some endpoints renamed
management:
  endpoints:
    web:
      base-path: /actuator
  endpoint:
    health:
      show-details: always
  # httptrace renamed to httpexchanges
  httpexchanges:
    enabled: true
```

| Old Endpoint | New Endpoint |
|--------------|--------------|
| `/actuator/httptrace` | `/actuator/httpexchanges` |
| `HttpTraceRepository` | `HttpExchangeRepository` |

## Phase 6: Hibernate 6 Migration

### Entity Changes

```java
// Hibernate 6 with Spring Boot 3.x
// ID generation strategy change
@Entity
public class Order {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)  // Preferred
    private Long id;

    // Hibernate 6: UUID generation
    @Id
    @GeneratedValue
    @UuidGenerator
    private UUID id;
}
```

### Key Hibernate 6 Changes

| Area | Change |
|------|--------|
| ID Generation | `GenerationType.AUTO` now maps to `SEQUENCE` by default (was `IDENTITY` with MySQL). Explicitly set strategy. |
| Implicit naming | `SpringPhysicalNamingStrategy` → `CamelCaseToUnderscoresNamingStrategy` |
| `@Type` annotation | `@Type(type="...")` string form removed. Use `@Type(JsonType.class)` with class reference |
| Criteria API | Uses Jakarta Persistence Criteria (package change) |
| `hibernate.dialect` | Auto-detected in most cases. Remove explicit dialect if using standard databases |
| Array/collection mapping | Some collection handling changed — test thoroughly |

### Hibernate Properties

```yaml
spring:
  jpa:
    properties:
      hibernate:
        # Remove explicit dialect (auto-detected in Hibernate 6)
        # dialect: org.hibernate.dialect.MySQL8Dialect  # REMOVE THIS
        format_sql: true
    # ID generation — avoid implicit strategy issues
    hibernate:
      ddl-auto: validate
```

## Phase 7: Spring Data Changes

### Repository Method Changes

```java
// Spring Data 3.x removes some deprecated methods
public interface UserRepository extends JpaRepository<User, Long> {

    // getById() deprecated → use getReferenceById()
    // findById() remains unchanged

    // deleteById behavior: no longer throws if entity not found
    // Previously threw EmptyResultDataAccessException
}
```

### Sort and Pageable

```java
// Spring Data 3.x — PageRequest.of() unchanged but
// Sort.by() with null handling changed
Pageable pageable = PageRequest.of(0, 20, Sort.by("createdAt").descending());
```

## Phase 8: Observability (Micrometer + Tracing)

Spring Boot 3.x replaces Spring Cloud Sleuth with Micrometer Tracing:

### Remove Sleuth

```xml
<!-- REMOVE these dependencies -->
<!--
<dependency>
    <groupId>org.springframework.cloud</groupId>
    <artifactId>spring-cloud-starter-sleuth</artifactId>
</dependency>
<dependency>
    <groupId>org.springframework.cloud</groupId>
    <artifactId>spring-cloud-sleuth-zipkin</artifactId>
</dependency>
-->

<!-- ADD Micrometer Tracing -->
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-actuator</artifactId>
</dependency>
<dependency>
    <groupId>io.micrometer</groupId>
    <artifactId>micrometer-tracing-bridge-brave</artifactId>
</dependency>
<dependency>
    <groupId>io.zipkin.reporter2</groupId>
    <artifactId>zipkin-reporter-brave</artifactId>
</dependency>
```

### Tracing Configuration

```yaml
management:
  tracing:
    sampling:
      probability: 1.0  # 100% in non-prod
  zipkin:
    tracing:
      endpoint: http://zipkin:9411/api/v2/spans
```

## Phase 9: Spring Cloud Compatibility

| Spring Boot | Spring Cloud Train |
|-------------|-------------------|
| 2.7.x | 2021.0.x (Jubilee) |
| 3.0.x | 2022.0.x (Kilburn) |
| 3.1.x | 2022.0.x (Kilburn) |
| 3.2.x | 2023.0.x (Leyton) |
| 3.3.x | 2023.0.x (Leyton) |
| 3.4.x | 2024.0.x |

### Spring Cloud Config Client Change

```yaml
# Spring Boot 3.x: bootstrap.yml/properties is DISABLED by default
# Option 1: Import config server explicitly
spring:
  config:
    import: "configserver:http://config-server:8888"

# Option 2: Re-enable bootstrap (not recommended for new apps)
# Add dependency: spring-cloud-starter-bootstrap
```

## Phase 10: Testing Changes

### JUnit and Mockito

```xml
<!-- Spring Boot 3.x uses JUnit 5 exclusively -->
<!-- Remove any JUnit 4 dependencies -->
<!--
<dependency>
    <groupId>junit</groupId>
    <artifactId>junit</artifactId>
</dependency>
-->

<!-- Mockito 5.x is pulled automatically -->
<!-- Remove explicit Mockito 3.x/4.x versions -->
```

### Test Annotation Changes

```java
// Spring Boot 2.x with JUnit 4
@RunWith(SpringRunner.class)
@SpringBootTest

// Spring Boot 3.x with JUnit 5
@SpringBootTest  // No @RunWith needed
@ExtendWith(SpringExtension.class)  // Only if not using @SpringBootTest
```

### MockMvc Changes

```java
// Spring Boot 3.x — MockMvc uses jakarta.servlet
import jakarta.servlet.http.HttpServletResponse;  // NOT javax

@AutoConfigureMockMvc
@SpringBootTest
class ApiControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @Test
    void testEndpoint() throws Exception {
        mockMvc.perform(get("/api/users"))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$[0].name").value("test"));
    }
}
```

## Gotchas

- **Never** rename `javax.sql`, `javax.crypto`, `javax.net`, or `javax.security.auth` packages. These are Java SE — not Java EE — and remain unchanged.
- **`@ConstructorBinding`** is no longer needed on single-constructor `@ConfigurationProperties` classes in Spring Boot 3.x. Remove it or compilation errors occur.
- **Auto-configuration** class registration moved from `spring.factories` to `META-INF/spring/org.springframework.boot.autoconfigure.AutoConfiguration.imports`. If you have custom starters, update the registration mechanism.
- **`HttpTraceRepository`** was renamed to `HttpExchangeRepository`. If you have custom trace storage, rename the interface implementation.
- **`@EnableGlobalMethodSecurity`** was replaced by `@EnableMethodSecurity`. The new annotation enables `@PreAuthorize`/`@PostAuthorize` by default but does NOT enable `@Secured` or `@RolesAllowed` by default — set `securedEnabled = true` explicitly if you use `@Secured`.
- **Spring Security CSRF** behavior changed. POST requests from Thymeleaf forms or AJAX that previously worked may fail with 403 if the CSRF token handling isn't updated.
- **Hibernate ID generation** — `GenerationType.AUTO` with MySQL previously used `IDENTITY` but now defaults to `TABLE` or `SEQUENCE`. Explicitly declare `IDENTITY` for MySQL/MariaDB to avoid schema issues.
- **`spring-boot-properties-migrator`** must be REMOVED before going to production. It adds startup overhead. Use it only during migration to detect deprecated property keys.
- **CyberArk Spring Boot Starter** — check if your CyberArk integration uses a Spring Boot starter. Custom starters must be recompiled against Spring Boot 3.x / Jakarta EE. If using property-based vault config, ensure the property keys haven't changed.
- **Logback 1.4+** used by Spring Boot 3.x requires Jakarta EE. If you have custom Logback appenders using `javax.servlet`, they must be updated.

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `ClassNotFoundException: javax.servlet.Filter` | Dependency still pulling old servlet API. Check `mvn dependency:tree` for `javax.servlet:javax.servlet-api` and exclude it |
| `NoSuchMethodError: WebSecurityConfigurerAdapter` | Class was removed. Rewrite to `SecurityFilterChain` bean pattern |
| `Parameter 0 of method required a bean of type 'EntityManagerFactory'` | Hibernate 6 with wrong dialect. Remove explicit `hibernate.dialect` property |
| `spring.config.import` required | Add `spring.config.import=optional:configserver:` or add bootstrap dependency |
| `.antMatchers()` not found | Renamed to `.requestMatchers()` in Spring Security 6 |
| `@ConstructorBinding` causing error | Remove the annotation (auto-detected for single constructors in 3.x) |
| Tests fail with `javax.persistence` not found | Test dependencies still reference old javax. Update test fixtures |
| `IllegalArgumentException: Not a managed type` | Entity class not scanned. Check `@EntityScan` base packages are correct after package restructuring |
| Flyway/Liquibase fails | Update to Flyway 9.x+ / Liquibase 4.x+ for Jakarta compatibility |
| `HttpMediaTypeNotSupportedException` on POST | Content-Type header handling is stricter in Spring 6. Ensure clients send proper Content-Type |

## Validation Checklist

After completing the migration:

- [ ] All `javax.persistence` → `jakarta.persistence` imports changed
- [ ] All `javax.servlet` → `jakarta.servlet` imports changed
- [ ] All `javax.validation` → `jakarta.validation` imports changed
- [ ] Spring Security config rewritten without `WebSecurityConfigurerAdapter`
- [ ] `application.properties` / `application.yml` keys updated
- [ ] `spring-boot-properties-migrator` removed from final build
- [ ] Hibernate dialect removed or updated
- [ ] Spring Cloud version aligned with Boot version
- [ ] Custom auto-configuration migrated from `spring.factories` to new imports file
- [ ] All tests pass on Spring Boot 3.x
- [ ] Actuator endpoints verified (`/actuator/health`, etc.)
- [ ] Tracing migrated from Sleuth to Micrometer Tracing (if applicable)
- [ ] CyberArk credential integration validated
- [ ] Snyk/SonarQube scan shows no new critical findings
- [ ] Application deployed and smoke-tested in lower environment

## References

- [Spring Boot 3.0 Migration Guide (Official)](https://github.com/spring-projects/spring-boot/wiki/Spring-Boot-3.0-Migration-Guide)
- [Spring Security 6 Migration](https://docs.spring.io/spring-security/reference/migration/index.html)
- [Hibernate 6 Migration Guide](https://github.com/hibernate/hibernate-orm/blob/6.0/migration-guide.adoc)
- [CyberArk Integration Notes](./references/cyberark-spring-boot3.md)
- [Spring Cloud Compatibility Matrix](./references/spring-cloud-matrix.md)
