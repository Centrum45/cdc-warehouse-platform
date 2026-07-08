package com.example.warehouse.config;

import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.stereotype.Component;

@Component
@ConfigurationProperties(prefix = "warehouse")
public class WarehouseProperties {
    private final Mysql mysql = new Mysql();
    private final Actions actions = new Actions();
    private final Validation validation = new Validation();

    public Mysql getMysql() { return mysql; }
    public Actions getActions() { return actions; }
    public Validation getValidation() { return validation; }

    public static class Mysql {
        private boolean fallbackDemoData;

        public boolean isFallbackDemoData() { return fallbackDemoData; }
        public void setFallbackDemoData(boolean fallbackDemoData) { this.fallbackDemoData = fallbackDemoData; }
    }

    public static class Actions {
        private boolean publicEnabled;

        public boolean isPublicEnabled() { return publicEnabled; }
        public void setPublicEnabled(boolean publicEnabled) { this.publicEnabled = publicEnabled; }
    }

    public static class Validation {
        private boolean enabled;
        private boolean requireProjectRoot = true;
        private boolean requireMysql = true;
        private boolean requireOpsDir;

        public boolean isEnabled() { return enabled; }
        public void setEnabled(boolean enabled) { this.enabled = enabled; }
        public boolean isRequireProjectRoot() { return requireProjectRoot; }
        public void setRequireProjectRoot(boolean requireProjectRoot) { this.requireProjectRoot = requireProjectRoot; }
        public boolean isRequireMysql() { return requireMysql; }
        public void setRequireMysql(boolean requireMysql) { this.requireMysql = requireMysql; }
        public boolean isRequireOpsDir() { return requireOpsDir; }
        public void setRequireOpsDir(boolean requireOpsDir) { this.requireOpsDir = requireOpsDir; }
    }
}
