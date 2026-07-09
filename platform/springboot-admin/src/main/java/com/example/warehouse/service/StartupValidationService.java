package com.example.warehouse.service;

import com.example.warehouse.config.WarehouseProperties;
import java.io.File;
import org.springframework.boot.ApplicationArguments;
import org.springframework.boot.ApplicationRunner;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;

@Service
public class StartupValidationService implements ApplicationRunner {
    private final WarehouseProperties warehouseProperties;
    private final CommandExecutorService commandExecutorService;
    private final JdbcTemplate jdbcTemplate;

    public StartupValidationService(
            WarehouseProperties warehouseProperties,
            CommandExecutorService commandExecutorService,
            JdbcTemplate jdbcTemplate) {
        this.warehouseProperties = warehouseProperties;
        this.commandExecutorService = commandExecutorService;
        this.jdbcTemplate = jdbcTemplate;
    }

    @Override
    public void run(ApplicationArguments args) {
        if (!warehouseProperties.getValidation().isEnabled()) {
            return;
        }
        File projectRoot = commandExecutorService.getProjectRoot();
        if (warehouseProperties.getValidation().isRequireProjectRoot() && !new File(projectRoot, "metadata").isDirectory()) {
            throw new IllegalStateException("Invalid warehouse.project-root: " + projectRoot.getAbsolutePath());
        }
        if (warehouseProperties.getValidation().isRequireOpsDir() && !new File(projectRoot, "data/ops").isDirectory()) {
            throw new IllegalStateException("Missing required ops dir: " + new File(projectRoot, "data/ops").getAbsolutePath());
        }
        if (warehouseProperties.getValidation().isRequireMysql()) {
            jdbcTemplate.queryForObject("select 1", Integer.class);
        }
        if (!warehouseProperties.getActions().isPublicEnabled()) {
            if ("admin123".equals(warehouseProperties.getAuth().getAdminPass())) {
                throw new IllegalStateException("ADMIN_PASS must be changed when public actions are disabled");
            }
            if (warehouseProperties.getAuth().getJwtSecret() == null || warehouseProperties.getAuth().getJwtSecret().length() < 32) {
                throw new IllegalStateException("JWT_SECRET must be at least 32 characters");
            }
            if (warehouseProperties.getAuth().getJwtSecret().contains("default-secret")) {
                throw new IllegalStateException("JWT_SECRET must not use a default value");
            }
        }
    }
}
