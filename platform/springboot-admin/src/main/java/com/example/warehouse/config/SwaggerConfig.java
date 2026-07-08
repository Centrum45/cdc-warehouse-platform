package com.example.warehouse.config;

import io.swagger.v3.oas.models.OpenAPI;
import io.swagger.v3.oas.models.info.Info;
import io.swagger.v3.oas.models.info.Contact;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class SwaggerConfig {

    @Bean
    public OpenAPI cdcWarehouseOpenAPI() {
        return new OpenAPI()
                .info(new Info()
                        .title("CDC Warehouse Platform API")
                        .description("Binlog-driven data warehouse management platform")
                        .version("0.1.0")
                        .contact(new Contact()
                                .name("CDC Warehouse Team")));
    }
}
