---
name: java-version-upgrade
description: 'Guide for migrating Java applications from Java 8 to Java 17 or Java 21. Use when upgrading JDK versions, fixing removed Java EE modules (javax.xml.bind, javax.activation, javax.xml.ws), resolving strong encapsulation errors, updating JVM flags, replacing Nashorn, fixing reflection access warnings, or modernizing enterprise Java codebases. Covers OpenJDK, OracleJDK, and Red Hat OpenJDK distributions.'
---

# Java 8 to Java 17/21 Version Upgrade

This skill provides step-by-step guidance for migrating enterprise Java applications from Java 8 to Java 17 (LTS) or Java 21 (LTS), covering removed APIs, module system changes, JVM flag updates, and dependency upgrades relevant to large-scale enterprise migration programs.

## When to Use This Skill

- Upgrading a project from Java 8 to Java 17 or Java 21
- Resolving compilation errors after changing JDK version in pom.xml or build.gradle
- Fixing `java.lang.reflect.InaccessibleObjectException` or illegal reflective access warnings
- Replacing removed Java EE modules (JAXB, JAX-WS, javax.activation)
- Updating JVM startup flags that were removed or changed
- Migrating from OracleJDK to OpenJDK (Red Hat, Adoptium, Amazon Corretto)
- Preparing codebase for Spring Boot 3.x upgrade (Java 17 is the minimum)

## Prerequisites

- Access to the application source code (Git repo)
- Maven 3.8+ or Gradle 7.x+ (for Java 17) / Gradle 8.x+ (for Java 21)
- RHMTA or similar migration analysis tool output (recommended)
- Existing test suite (unit + integration) for validation

## Phase 1: Assessment

Before making code changes, assess the migration scope:

### Run Dependency Analysis

```bash
# Maven: generate dependency tree
mvn dependency:tree -DoutputType=text > dependency-tree.txt

# Check for JDK internal API usage
jdeps --jdk-internals --multi-release 17 -cp target/classes target/*.jar
```

### Identify Breaking Areas

| Category | Java 8 → 17 Impact | Java 17 → 21 Impact |
|----------|--------------------|--------------------|
| Removed Java EE modules | High - manual fix required | None |
| Strong encapsulation | High - reflection breaks | None (already enforced) |
| Removed JVM flags | Medium - startup failures | Low |
| Deprecated APIs | Medium | Low - some removals |
| Security Manager | Low (deprecated in 17) | High (removed in 21) |
| Nashorn engine | High if used | N/A (already removed) |

## Phase 2: Build Configuration

### Maven pom.xml Updates

```xml
<!-- Update compiler settings -->
<properties>
    <java.version>17</java.version>
    <maven.compiler.source>17</maven.compiler.source>
    <maven.compiler.target>17</maven.compiler.target>
    <maven.compiler.release>17</maven.compiler.release>
</properties>

<!-- Update Maven plugins for Java 17 compatibility -->
<plugin>
    <groupId>org.apache.maven.plugins</groupId>
    <artifactId>maven-compiler-plugin</artifactId>
    <version>3.13.0</version>
    <configuration>
        <release>17</release>
    </configuration>
</plugin>

<plugin>
    <groupId>org.apache.maven.plugins</groupId>
    <artifactId>maven-surefire-plugin</artifactId>
    <version>3.5.2</version>
</plugin>

<plugin>
    <groupId>org.apache.maven.plugins</groupId>
    <artifactId>maven-failsafe-plugin</artifactId>
    <version>3.5.2</version>
</plugin>
```

### For Java 21

```xml
<properties>
    <java.version>21</java.version>
    <maven.compiler.release>21</maven.compiler.release>
</properties>
```

## Phase 3: Removed Java EE Modules

These modules were included in Java 8 but removed in Java 11+. You must add explicit dependencies:

### JAXB (javax.xml.bind)

```xml
<!-- Replace removed javax.xml.bind module -->
<dependency>
    <groupId>jakarta.xml.bind</groupId>
    <artifactId>jakarta.xml.bind-api</artifactId>
    <version>4.0.2</version>
</dependency>
<dependency>
    <groupId>org.glassfish.jaxb</groupId>
    <artifactId>jaxb-runtime</artifactId>
    <version>4.0.5</version>
    <scope>runtime</scope>
</dependency>
```

### JAX-WS (javax.xml.ws)

```xml
<!-- Replace removed javax.xml.ws module -->
<dependency>
    <groupId>jakarta.xml.ws</groupId>
    <artifactId>jakarta.xml.ws-api</artifactId>
    <version>4.0.2</version>
</dependency>
<dependency>
    <groupId>com.sun.xml.ws</groupId>
    <artifactId>jaxws-runtime</artifactId>
    <version>4.0.3</version>
</dependency>
```

### javax.activation

```xml
<dependency>
    <groupId>jakarta.activation</groupId>
    <artifactId>jakarta.activation-api</artifactId>
    <version>2.1.3</version>
</dependency>
```

### javax.annotation (Common Annotations)

```xml
<dependency>
    <groupId>jakarta.annotation</groupId>
    <artifactId>jakarta.annotation-api</artifactId>
    <version>3.0.0</version>
</dependency>
```

### CORBA

CORBA was removed entirely. If the application uses CORBA:
- Migrate to gRPC, REST, or message-based communication
- Use GlassFish CORBA ORB as a standalone dependency (last resort)

## Phase 4: Strong Encapsulation Fixes

Java 17 enforces strong encapsulation by default. Code using internal JDK APIs via reflection will fail.

### Common Violations and Fixes

| Internal API Used | Replacement |
|-------------------|-------------|
| `sun.misc.Unsafe` | `java.lang.invoke.VarHandle` or `java.util.concurrent.atomic` |
| `sun.misc.BASE64Encoder` | `java.util.Base64` |
| `sun.reflect.ReflectionFactory` | Standard reflection or MethodHandles |
| `com.sun.org.apache.xerces` | Use standard `javax.xml.parsers` |
| `sun.security.x509` | Use `java.security.cert` APIs |

### If You Cannot Immediately Fix (Temporary Workaround)

Add JVM flags to open internal modules. This is a **temporary** measure only:

```bash
--add-opens java.base/java.lang=ALL-UNNAMED
--add-opens java.base/java.lang.reflect=ALL-UNNAMED
--add-opens java.base/java.util=ALL-UNNAMED
--add-opens java.base/sun.net.www.protocol.https=ALL-UNNAMED
```

In Maven surefire:

```xml
<plugin>
    <groupId>org.apache.maven.plugins</groupId>
    <artifactId>maven-surefire-plugin</artifactId>
    <configuration>
        <argLine>
            --add-opens java.base/java.lang=ALL-UNNAMED
            --add-opens java.base/java.util=ALL-UNNAMED
        </argLine>
    </configuration>
</plugin>
```

## Phase 5: JVM Flag Updates

### Removed Flags (will cause startup failure)

| Removed Flag | Action |
|--------------|--------|
| `-XX:+UseConcMarkSweepGC` | Replace with `-XX:+UseG1GC` or `-XX:+UseZGC` |
| `-XX:+UseParNewGC` | Remove (G1 is default) |
| `-XX:+CMSParallelRemarkEnabled` | Remove |
| `-XX:+UseCMSInitiatingOccupancyOnly` | Remove |
| `-XX:CMSInitiatingOccupancyFraction=N` | Use `-XX:InitiatingHeapOccupancyPercent=N` for G1 |
| `-XX:+PrintGCDetails` | Use `-Xlog:gc*` |
| `-XX:+PrintGCDateStamps` | Use `-Xlog:gc*::time` |
| `-verbose:gc` | Use `-Xlog:gc` |
| `-XX:+PrintTenuringDistribution` | Use `-Xlog:gc+age*=trace` |
| `-Xloggc:/path/file` | Use `-Xlog:gc*:file=/path/file` |

### Recommended GC Configuration for Java 17

```bash
# For latency-sensitive applications (microservices, APIs)
-XX:+UseZGC -XX:+ZGenerational -Xms512m -Xmx2g

# For throughput-oriented applications (batch, ETL)
-XX:+UseG1GC -XX:MaxGCPauseMillis=200 -Xms1g -Xmx4g
```

### Recommended GC for Java 21

```bash
# ZGC Generational is production-ready in 21
-XX:+UseZGC -XX:+ZGenerational -Xms512m -Xmx2g

# Virtual Threads (Java 21) - increase carrier thread pool if needed
-Djdk.virtualThreadScheduler.parallelism=16
```

## Phase 6: Nashorn Replacement

If the application uses Nashorn JavaScript engine (removed in Java 15):

```xml
<!-- GraalVM JavaScript as Nashorn replacement -->
<dependency>
    <groupId>org.graalvm.js</groupId>
    <artifactId>js</artifactId>
    <version>23.0.4</version>
</dependency>
<dependency>
    <groupId>org.graalvm.js</groupId>
    <artifactId>js-scriptengine</artifactId>
    <version>23.0.4</version>
</dependency>
```

Code change:

```java
// Before (Java 8 with Nashorn)
ScriptEngine engine = new ScriptEngineManager().getEngineByName("nashorn");

// After (Java 17+ with GraalVM JS)
ScriptEngine engine = new ScriptEngineManager().getEngineByName("graal.js");
```

## Phase 7: Source Code Modernization (Optional)

These are not required for compilation but improve code quality:

| Old Pattern | Modern Replacement | Since |
|-------------|-------------------|-------|
| Anonymous inner class (single method) | Lambda expression | Java 8 |
| Builder boilerplate POJO | `record` | Java 16 |
| `instanceof` + cast | Pattern matching `instanceof` | Java 16 |
| Multi-line string concatenation | Text blocks `"""` | Java 15 |
| Switch with fall-through | Switch expressions | Java 14 |
| `var` for local variables | Type inference | Java 10 |
| Sealed class hierarchies | `sealed` / `permits` | Java 17 |

## Gotchas

- **Never** upgrade directly from Java 8 to 21 in one jump if the app uses Spring Boot 2.x. Upgrade Java first (to 17), stabilize, then upgrade Spring Boot to 3.x, then optionally move to Java 21.
- **`--illegal-access=permit`** flag was removed in Java 17. If your Java 11/16 build relied on it, the app will hard-fail on 17. You must fix the underlying reflection usage or add specific `--add-opens`.
- **Lombok versions below 1.18.22** do not compile on Java 17. Upgrade Lombok to 1.18.30+ immediately.
- **ASM/ByteBuddy/cglib** libraries older than 2022 do not support Java 17 bytecode (version 61). This commonly surfaces through Hibernate, Mockito, or Spring AOP. Update these transitively via framework upgrades.
- **Maven Enforcer Plugin** may reject the build if `requireJavaVersion` is still set to `[1.8,)`. Update the rule to `[17,)`.
- **Gradle** versions below 7.3 do not support Java 17. Gradle below 8.5 does not support Java 21.
- **Jackson Databind** versions below 2.13 have issues on Java 17 with records and strong encapsulation. Use 2.17+.
- **JAXB xjc code generation** — if you generate Java classes from XSD, the Maven plugin must also be updated to Jakarta JAXB 4.x tooling.
- **CyberArk Java SDK** — verify compatibility with Java 17. Some older CyberArk Credential Provider JNI bindings require `--add-opens` for `java.base/java.lang`. See [CyberArk integration reference](./references/cyberark-integration.md).

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `java.lang.reflect.InaccessibleObjectException` | Add specific `--add-opens` for the module/package, then plan to remove internal API usage |
| `NoSuchMethodError` in framework code | Library version too old for Java 17 bytecode. Update the framework |
| `ClassNotFoundException: javax.xml.bind.*` | Add JAXB Jakarta dependencies (see Phase 3) |
| `UnsupportedClassVersionError: class file version 61` | A dependency was compiled with Java 17 but running on Java 8 runtime. Ensure ALL environments use Java 17 |
| Maven build OOM | Add `MAVEN_OPTS=-Xmx2g` — Java 17 metaspace behavior differs |
| `--illegal-access=permit` not recognized | This flag was removed. Replace with specific `--add-opens` flags |
| Mockito/PowerMock failures | Upgrade to Mockito 5.x, remove PowerMock entirely (use Mockito inline mock maker) |
| Spring Boot 2.x fails on Java 17 | Minimum Spring Boot 2.7.x for Java 17 support. Upgrade Spring Boot first |

## Validation Checklist

After completing the migration:

- [ ] Application compiles without errors on Java 17/21
- [ ] All unit tests pass
- [ ] All integration tests pass
- [ ] No `--add-opens` flags remain as permanent workarounds (track as tech debt)
- [ ] JVM startup flags reviewed and updated
- [ ] GC configuration validated for target environment
- [ ] No `WARNING: An illegal reflective access operation has occurred` in logs
- [ ] Dependency tree shows no Java 8-only libraries
- [ ] Snyk/SonarQube scan passes with no new critical findings
- [ ] Performance baseline comparable to Java 8 version (or better)
- [ ] CyberArk credential retrieval validated

## References

- [Oracle JDK 17 Migration Guide](https://docs.oracle.com/en/java/javase/17/migrate/migrating-jdk-8-later-jdk-releases.html)
- [Red Hat OpenJDK 17 Migration Guide](https://docs.redhat.com/en/documentation/red_hat_build_of_openjdk/17/html-single/migrating_to_red_hat_build_of_openjdk_17_from_earlier_versions/index)
- [CyberArk Integration Notes](./references/cyberark-integration.md)
- [JVM Flags Migration Matrix](./references/jvm-flags-matrix.md)
