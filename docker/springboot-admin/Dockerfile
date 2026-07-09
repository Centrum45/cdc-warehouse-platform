# syntax=docker/dockerfile:1.7
FROM maven:3.9.8-eclipse-temurin-8 AS build
WORKDIR /workspace/platform/springboot-admin
COPY platform/springboot-admin/pom.xml .
COPY platform/springboot-admin/src ./src
RUN --mount=type=cache,target=/root/.m2 mvn -B -DskipTests package

FROM eclipse-temurin:8-jre
RUN apt-get update \
    && apt-get install -y --no-install-recommends python3 python3-yaml \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY --from=build /workspace/platform/springboot-admin/target/cdc-warehouse-admin-0.1.0.jar /app/app.jar
EXPOSE 8080
ENTRYPOINT ["java", "-jar", "/app/app.jar"]
