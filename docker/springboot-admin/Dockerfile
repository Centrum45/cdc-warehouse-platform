FROM maven:3.9.8-eclipse-temurin-8 AS build
WORKDIR /workspace/platform/springboot-admin
COPY platform/springboot-admin/pom.xml .
RUN mvn -q -DskipTests dependency:go-offline
COPY platform/springboot-admin/src ./src
RUN mvn -q -DskipTests package

FROM eclipse-temurin:8-jre
WORKDIR /app
COPY --from=build /workspace/platform/springboot-admin/target/cdc-warehouse-admin-0.1.0.jar /app/app.jar
EXPOSE 8080
ENTRYPOINT ["java", "-jar", "/app/app.jar"]
