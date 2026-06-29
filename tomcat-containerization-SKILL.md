---
name: tomcat-containerization
description: 'Guide for migrating Java applications from Tomcat VM deployments to Tomcat containers (Docker/Kubernetes). Use when containerizing Tomcat 9 or 10 applications, creating Dockerfiles for Java web apps, migrating from WAS Liberty or WebLogic to Spring Boot on Tomcat, converting WAR deployments to embedded Tomcat JARs, sizing container resources from VM utilization data, configuring health checks and readiness probes, or building lightweight Java runtime containers with OpenJDK/JRE. Covers OracleJDK to OpenJDK migration, multi-stage Docker builds, and Kubernetes deployment patterns.'
---

# Tomcat VM to Tomcat Container Migration

This skill provides step-by-step guidance for migrating enterprise Java applications from traditional Tomcat VM deployments to containerized Tomcat (Docker/Kubernetes), covering Dockerfile creation, resource sizing, health checks, security hardening, and enterprise deployment patterns. Includes patterns for migrating from WAS Liberty and WebLogic to Spring Boot on Tomcat containers.

## When to Use This Skill

- Containerizing an existing Tomcat 9/10 application running on a VM
- Creating a Dockerfile for a Java WAR or Spring Boot JAR application
- Migrating from external Tomcat WAR deployment to embedded Tomcat (Spring Boot JAR)
- Sizing container CPU/memory based on existing VM utilization data (Truesight/Server-Info)
- Configuring Kubernetes liveness, readiness, and startup probes for Tomcat apps
- Migrating from OracleJDK to OpenJDK/Eclipse Temurin in a container image
- Converting WAS Liberty or WebLogic applications to Spring Boot on Tomcat
- Building minimal/distroless Java container images for production

## Migration Patterns Overview

| Pattern | Source | Target | Complexity |
|---------|--------|--------|-----------|
| Pattern A | Tomcat 9 VM + WAR | Tomcat 10 Container + WAR | Low |
| Pattern B | Tomcat VM + WAR | Spring Boot Embedded Tomcat (JAR) | Medium |
| Pattern C | WAS Liberty/WebLogic + EAR | Spring Boot on Tomcat Container | High |
| Pattern D | OracleJDK + Tomcat VM | OpenJDK/Temurin + Tomcat Container | Low-Medium |

## Pattern A: Tomcat WAR to Tomcat Container

### Dockerfile — Tomcat 10 with Java 17

```dockerfile
# Multi-stage build for security and size
FROM eclipse-temurin:17-jdk AS builder

WORKDIR /app
COPY . .
RUN ./mvnw clean package -DskipTests -Dmaven.repo.local=.m2

# Production image — minimal runtime
FROM tomcat:10.1-jre17-temurin-jammy

# Remove default webapps (security hardening)
RUN rm -rf /usr/local/tomcat/webapps/*
RUN rm -rf /usr/local/tomcat/webapps.dist

# Remove unnecessary Tomcat components
RUN rm -rf /usr/local/tomcat/bin/*.bat
RUN rm -f /usr/local/tomcat/bin/tomcat-native.tar.gz

# Copy WAR to webapps
COPY --from=builder /app/target/*.war /usr/local/tomcat/webapps/ROOT.war

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser -d /usr/local/tomcat appuser
RUN chown -R appuser:appuser /usr/local/tomcat
USER appuser

# Expose HTTP port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 --start-period=60s \
    CMD curl -f http://localhost:8080/actuator/health || exit 1

CMD ["catalina.sh", "run"]
```

### Dockerfile — Tomcat 10 with Java 21

```dockerfile
FROM eclipse-temurin:21-jre-noble AS runtime

ENV CATALINA_HOME=/usr/local/tomcat
ENV PATH=$CATALINA_HOME/bin:$PATH

# Install Tomcat 10.1
ARG TOMCAT_VERSION=10.1.34
RUN mkdir -p "$CATALINA_HOME" \
    && curl -fsSL "https://dlcdn.apache.org/tomcat/tomcat-10/v${TOMCAT_VERSION}/bin/apache-tomcat-${TOMCAT_VERSION}.tar.gz" \
       | tar -xz --strip-components=1 -C "$CATALINA_HOME" \
    && rm -rf "$CATALINA_HOME/webapps.dist" "$CATALINA_HOME/webapps/*" \
    && rm -rf "$CATALINA_HOME/bin/*.bat"

COPY target/*.war $CATALINA_HOME/webapps/ROOT.war

RUN groupadd -r appuser && useradd -r -g appuser appuser \
    && chown -R appuser:appuser $CATALINA_HOME
USER appuser

EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=10s --retries=3 --start-period=60s \
    CMD curl -f http://localhost:8080/actuator/health || exit 1
CMD ["catalina.sh", "run"]
```

## Pattern B: WAR to Embedded Tomcat (Spring Boot JAR)

Converting from external Tomcat WAR deployment to Spring Boot executable JAR with embedded Tomcat.

### Step 1: Remove Tomcat Dependency Conflict

```xml
<!-- In pom.xml: Mark Tomcat as provided for WAR, embedded for JAR -->
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-web</artifactId>
    <!-- Remove any exclusion of tomcat-embed if building as JAR -->
</dependency>

<!-- Change packaging from WAR to JAR -->
<packaging>jar</packaging>

<!-- Remove servlet API dependency (provided by embedded Tomcat) -->
<!--
<dependency>
    <groupId>jakarta.servlet</groupId>
    <artifactId>jakarta.servlet-api</artifactId>
    <scope>provided</scope>  REMOVE THIS
</dependency>
-->
```

### Step 2: Remove ServletInitializer

```java
// DELETE this class if it exists — only needed for WAR deployment
// public class ServletInitializer extends SpringBootServletInitializer {
//     @Override
//     protected SpringApplicationBuilder configure(SpringApplicationBuilder app) {
//         return app.sources(Application.class);
//     }
// }
```

### Step 3: Dockerfile for Spring Boot JAR

```dockerfile
# Multi-stage build
FROM eclipse-temurin:17-jdk-jammy AS builder

WORKDIR /app
COPY pom.xml .
COPY .mvn .mvn
COPY mvnw .
RUN chmod +x mvnw && ./mvnw dependency:go-offline -B

COPY src ./src
RUN ./mvnw clean package -DskipTests -Dmaven.repo.local=.m2

# Layered JAR extraction for better Docker layer caching
RUN java -Djarmode=layertools -jar target/*.jar extract --destination extracted

# Production runtime
FROM eclipse-temurin:17-jre-jammy

# Security: non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser
WORKDIR /app

# Copy layers in order of change frequency (least → most)
COPY --from=builder /app/extracted/dependencies/ ./
COPY --from=builder /app/extracted/spring-boot-loader/ ./
COPY --from=builder /app/extracted/snapshot-dependencies/ ./
COPY --from=builder /app/extracted/application/ ./

RUN chown -R appuser:appuser /app
USER appuser

EXPOSE 8080

# JVM configuration for containers
ENV JAVA_OPTS="-XX:+UseZGC \
    -XX:+ZGenerational \
    -XX:MaxRAMPercentage=75.0 \
    -XX:InitialRAMPercentage=50.0 \
    -Djava.security.egd=file:/dev/./urandom"

HEALTHCHECK --interval=30s --timeout=10s --retries=3 --start-period=90s \
    CMD curl -f http://localhost:8080/actuator/health/liveness || exit 1

ENTRYPOINT ["sh", "-c", "java $JAVA_OPTS org.springframework.boot.loader.launch.JarLauncher"]
```

## Pattern C: WAS Liberty/WebLogic to Spring Boot on Tomcat

### Assessment Checklist

Before migrating, identify J2EE/Jakarta EE features in use:

| Feature | WAS/WebLogic | Spring Boot Equivalent |
|---------|--------------|----------------------|
| EJB (Stateless) | `@Stateless` | `@Service` + `@Transactional` |
| EJB (Stateful) | `@Stateful` | `@Component` + `@SessionScope` |
| EJB Timer | `@Schedule` | `@Scheduled` or Spring Quartz |
| JMS MDB | `@MessageDriven` | `@JmsListener` |
| JPA EntityManager | Container-managed | Spring Data JPA |
| JNDI Datasource | `java:comp/env/jdbc/myDS` | `spring.datasource.*` properties |
| JSF/Facelets | `*.xhtml` pages | Thymeleaf / React / Angular |
| Servlet Filters | `web.xml` registration | `@Component` + `FilterRegistrationBean` |
| Security Realm | WAS admin console | Spring Security `SecurityFilterChain` |
| WebSocket | `@ServerEndpoint` | `@EnableWebSocket` + Spring STOMP |

### JNDI to Spring Properties Conversion

```java
// Before (WAS/WebLogic JNDI lookup)
Context ctx = new InitialContext();
DataSource ds = (DataSource) ctx.lookup("java:comp/env/jdbc/appDB");

// After (Spring Boot externalized config)
// application.yml:
// spring:
//   datasource:
//     url: jdbc:oracle:thin:@host:1521:DB
//     driver-class-name: oracle.jdbc.OracleDriver
//     hikari:
//       maximum-pool-size: 20
//       minimum-idle: 5

@Configuration
public class DataSourceConfig {
    // Spring Boot auto-configures DataSource from properties
    // No manual bean definition needed for standard cases
}
```

### EJB to Spring Service Conversion

```java
// Before (EJB in WAS/WebLogic)
@Stateless
@TransactionAttribute(TransactionAttributeType.REQUIRED)
public class OrderServiceBean implements OrderService {
    @PersistenceContext
    private EntityManager em;

    public Order createOrder(OrderRequest request) {
        Order order = new Order(request);
        em.persist(order);
        return order;
    }
}

// After (Spring Service)
@Service
@Transactional
public class OrderService {

    private final OrderRepository orderRepository;

    public OrderService(OrderRepository orderRepository) {
        this.orderRepository = orderRepository;
    }

    public Order createOrder(OrderRequest request) {
        Order order = new Order(request);
        return orderRepository.save(order);
    }
}
```

## Pattern D: OracleJDK to OpenJDK in Container

### Base Image Selection

| Distribution | Image | Use Case |
|-------------|-------|----------|
| Eclipse Temurin | `eclipse-temurin:17-jre-jammy` | Recommended default |
| Red Hat UBI OpenJDK | `registry.access.redhat.com/ubi9/openjdk-17-runtime` | Red Hat environments |
| Amazon Corretto | `amazoncorretto:17-alpine` | AWS deployments |
| Microsoft OpenJDK | `mcr.microsoft.com/openjdk/jdk:17-ubuntu` | Azure deployments |

### Oracle-Specific API Replacements

| OracleJDK Feature | OpenJDK Alternative |
|-------------------|-------------------|
| `sun.misc.Unsafe` | `VarHandle` / `MethodHandles` |
| Java Flight Recorder (commercial) | JFR is free in OpenJDK 11+ |
| `jdk.management.cmm` | Not needed (use standard MBeans) |
| Oracle-specific GC tuning | Standard GC flags work identically |
| `tools.jar` | Removed in Java 9+ (modules system) |

## Container Resource Sizing

### Converting VM Utilization to Container Limits

Use Truesight/Server-Info data to calculate container resources:

| VM Metric | Container Equivalent | Formula |
|-----------|---------------------|---------|
| VM CPU (cores allocated) | `resources.requests.cpu` | P95 utilization × cores |
| VM CPU peak | `resources.limits.cpu` | P99 utilization × cores × 1.2 |
| VM Memory (allocated) | `resources.limits.memory` | JVM heap + 30% overhead |
| VM Memory (used P95) | `resources.requests.memory` | P95 usage + 256Mi buffer |

### Example Calculation

```
VM specs: 4 CPU cores, 8 GB RAM
Truesight P95: CPU 35%, Memory 62%

Container sizing:
  CPU request: 0.35 × 4 = 1.4 → round to 1500m
  CPU limit:   0.50 × 4 = 2.0 → 2000m (headroom for spikes)
  Memory request: 8GB × 0.62 = 4.96 GB → 5Gi
  Memory limit:   JVM heap (4G) + metaspace (512M) + native (512M) = 5Gi

JVM heap: 75% of container memory limit
  -XX:MaxRAMPercentage=75.0  → 3.75 GB heap in 5Gi container
```

### JVM Container-Aware Settings

```bash
# Container-optimized JVM flags (Java 17+)
JAVA_OPTS="\
  -XX:+UseContainerSupport \
  -XX:MaxRAMPercentage=75.0 \
  -XX:InitialRAMPercentage=50.0 \
  -XX:+UseZGC \
  -XX:+ZGenerational \
  -XX:+ExitOnOutOfMemoryError \
  -Djava.security.egd=file:/dev/./urandom \
  -Dfile.encoding=UTF-8"
```

**Key flags explained:**

| Flag | Purpose |
|------|---------|
| `UseContainerSupport` | JVM respects container cgroup limits (default on in 17+) |
| `MaxRAMPercentage=75` | Heap uses 75% of container memory (leave room for metaspace, native, stack) |
| `ExitOnOutOfMemoryError` | Container dies on OOM so orchestrator can restart cleanly |
| `java.security.egd` | Faster random number generation in containers |

## Kubernetes Deployment

### Deployment Manifest

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: myapp
  labels:
    app: myapp
spec:
  replicas: 2
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxUnavailable: 0
      maxSurge: 1
  selector:
    matchLabels:
      app: myapp
  template:
    metadata:
      labels:
        app: myapp
    spec:
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
        fsGroup: 1000
      containers:
        - name: myapp
          image: registry.citi.com/myapp:1.0.0
          ports:
            - containerPort: 8080
              protocol: TCP
          resources:
            requests:
              cpu: "1500m"
              memory: "5Gi"
            limits:
              cpu: "2000m"
              memory: "5Gi"
          env:
            - name: JAVA_OPTS
              value: >-
                -XX:+UseZGC
                -XX:+ZGenerational
                -XX:MaxRAMPercentage=75.0
                -XX:+ExitOnOutOfMemoryError
            - name: SPRING_PROFILES_ACTIVE
              value: "container,prod"
          livenessProbe:
            httpGet:
              path: /actuator/health/liveness
              port: 8080
            initialDelaySeconds: 90
            periodSeconds: 30
            timeoutSeconds: 10
            failureThreshold: 3
          readinessProbe:
            httpGet:
              path: /actuator/health/readiness
              port: 8080
            initialDelaySeconds: 60
            periodSeconds: 10
            timeoutSeconds: 5
            failureThreshold: 3
          startupProbe:
            httpGet:
              path: /actuator/health/liveness
              port: 8080
            initialDelaySeconds: 30
            periodSeconds: 10
            failureThreshold: 12  # 30s + (12 × 10s) = 150s max startup
          volumeMounts:
            - name: tmp
              mountPath: /tmp
      volumes:
        - name: tmp
          emptyDir: {}
```

### Health Check Configuration (Spring Boot)

```yaml
# application-container.yml (activated by SPRING_PROFILES_ACTIVE=container)
management:
  endpoints:
    web:
      exposure:
        include: health,info,prometheus,metrics
  endpoint:
    health:
      probes:
        enabled: true  # Enables /health/liveness and /health/readiness
      show-details: when-authorized
  health:
    livenessState:
      enabled: true
    readinessState:
      enabled: true

server:
  shutdown: graceful

spring:
  lifecycle:
    timeout-per-shutdown-phase: 30s
```

## Tomcat Configuration in Container

### server.xml Tuning for Containers

```xml
<!-- Optimized Tomcat connector for containerized deployment -->
<Connector port="8080"
           protocol="org.apache.coyote.http11.Http11NioProtocol"
           maxThreads="200"
           minSpareThreads="25"
           acceptCount="100"
           connectionTimeout="20000"
           maxKeepAliveRequests="100"
           keepAliveTimeout="15000"
           compression="on"
           compressionMinSize="2048"
           compressibleMimeType="text/html,text/xml,text/plain,text/css,application/json,application/javascript"/>
```

### Spring Boot Embedded Tomcat Equivalent

```yaml
server:
  tomcat:
    threads:
      max: 200
      min-spare: 25
    accept-count: 100
    connection-timeout: 20000
    max-keep-alive-requests: 100
    keep-alive-timeout: 15000
  compression:
    enabled: true
    min-response-size: 2048
    mime-types: text/html,text/xml,text/plain,text/css,application/json,application/javascript
```

## Security Hardening

### Container Image Security

```dockerfile
# Run as non-root
USER 1000:1000

# Read-only filesystem where possible
# Mount /tmp as writable volume in K8s

# No shell in production (distroless approach)
FROM gcr.io/distroless/java17-debian12
COPY --from=builder /app/target/*.jar /app/app.jar
ENTRYPOINT ["java", "-jar", "/app/app.jar"]
```

### Security Checklist for Containers

- [ ] Non-root user in Dockerfile
- [ ] No secrets in image layers (use K8s Secrets or CyberArk sidecar)
- [ ] Base image regularly updated (Snyk/Trivy scan)
- [ ] Read-only root filesystem in pod spec
- [ ] Network policies restrict pod-to-pod communication
- [ ] Service mesh (Istio/Linkerd) for mTLS between services
- [ ] Pod security standards enforced (restricted profile)

## CyberArk Integration in Containers

### Pattern 1: Init Container (Recommended)

```yaml
initContainers:
  - name: cyberark-credential-provider
    image: registry.citi.com/cyberark/cp-init:latest
    env:
      - name: VAULT_ADDR
        value: "https://vault.citi.internal:443"
      - name: SAFE_NAME
        value: "AppCredentials"
      - name: OBJECT_NAME
        value: "myapp-db-password"
    volumeMounts:
      - name: credentials
        mountPath: /credentials
containers:
  - name: myapp
    env:
      - name: DB_PASSWORD_FILE
        value: /credentials/db-password
    volumeMounts:
      - name: credentials
        mountPath: /credentials
        readOnly: true
volumes:
  - name: credentials
    emptyDir:
      medium: Memory  # tmpfs — not written to disk
```

### Pattern 2: Spring Boot CyberArk Property Source

```java
@Configuration
public class CyberArkConfig {

    @Bean
    public PropertySourceLocator cyberArkPropertySource() {
        // Read credentials from CyberArk at startup
        // Populate as Spring properties: spring.datasource.password, etc.
        return new CyberArkPropertySourceLocator();
    }
}
```

```yaml
# application-container.yml
spring:
  datasource:
    password: ${CYBERARK_DB_PASSWORD}  # Injected by init container or sidecar
```

## Gotchas

- **Never** use `latest` tag for base images in production. Pin to specific digest or version (e.g., `eclipse-temurin:17.0.13_11-jre-jammy`).
- **`MaxRAMPercentage=75`** means 75% of the container limit, not the request. If limits and requests differ significantly, the JVM may allocate more heap than the scheduler expected, causing node-level memory pressure.
- **Tomcat 10.0.x vs 10.1.x** — Tomcat 10.0.x implements Jakarta EE 9 (namespace only), while Tomcat 10.1.x implements Jakarta EE 10 (API additions). Spring Boot 3.x requires Tomcat 10.1+ (Jakarta EE 10).
- **WAR file naming** — Deploying as `ROOT.war` makes the app available at `/`. Any other name becomes the context path (e.g., `myapp.war` → `/myapp`). This may break existing client URLs.
- **Session persistence** — VM Tomcat often uses file-based session persistence. In containers, sessions are lost on restart. Use Redis/Hazelcast for distributed sessions or make the app stateless.
- **Timezone** — Container images default to UTC. If the app expects a specific timezone, set `TZ` environment variable or `-Duser.timezone=America/New_York`.
- **File uploads** — `/tmp` in containers is ephemeral. Use a persistent volume or object storage (S3) for file uploads.
- **Logging** — Do NOT write logs to files inside the container. Write to stdout/stderr and let the container runtime (Docker/K8s) handle log collection.
- **Graceful shutdown** — Without `server.shutdown=graceful`, in-flight requests are killed during rolling updates. Always configure graceful shutdown with appropriate timeout.
- **DNS resolution** — Kubernetes uses `ndots:5` by default, causing 5 DNS lookups for external domains. Set `dnsConfig.options: [{name: ndots, value: "2"}]` in pod spec for apps making many external calls.
- **CyberArk timeout** — CyberArk credential retrieval adds 5-15s to startup time. Account for this in `startupProbe.initialDelaySeconds`.

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Container OOMKilled but heap not full | Native memory leak or metaspace growth. Add `-XX:NativeMemoryTracking=summary` and increase memory limit |
| App starts on VM but fails in container | Check for hardcoded file paths, hostnames, or network assumptions |
| Startup takes 2+ minutes | Enable Spring Boot lazy initialization: `spring.main.lazy-initialization=true` for non-prod |
| Health checks fail intermittently | Increase `timeoutSeconds` or check GC pauses with `-Xlog:gc*` |
| `java.net.UnknownHostException` for internal services | DNS resolution issue. Check K8s service names and namespace |
| `java.io.IOException: No space left on device` | Container filesystem full. Check log file writes or use `emptyDir` volume for `/tmp` |
| Tomcat stops accepting connections | Thread pool exhausted. Increase `server.tomcat.threads.max` or check for thread leaks |
| Permission denied on file writes | Running as non-root. Ensure writable paths are volumes with correct `fsGroup` |
| CyberArk init container timeout | Vault network unreachable from pod. Check network policies and init container timeout settings |
| Image pull fails | Registry authentication. Ensure `imagePullSecrets` configured in service account |

## Validation Checklist

After completing containerization:

- [ ] Application starts successfully in container
- [ ] All endpoints respond correctly (smoke test)
- [ ] Health/readiness probes return 200
- [ ] Container resource limits match VM utilization profile
- [ ] JVM respects container memory limits (not using host memory)
- [ ] Non-root user enforced
- [ ] No secrets in image layers
- [ ] Graceful shutdown handles in-flight requests
- [ ] Logs go to stdout/stderr (not files)
- [ ] Rolling update completes without downtime
- [ ] CyberArk credentials retrieved successfully at startup
- [ ] Snyk/Trivy scan passes on container image
- [ ] Performance comparable to VM deployment
- [ ] Session handling works correctly (distributed or stateless)

## References

- [Docker Java Best Practices](https://docs.docker.com/guides/java/containerize/)
- [Eclipse Temurin Docker Images](https://hub.docker.com/_/eclipse-temurin)
- [Kubernetes Probes Configuration](https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/)
- [CyberArk Container Integration](./references/cyberark-container-patterns.md)
- [Resource Sizing Calculator](./references/resource-sizing-guide.md)
