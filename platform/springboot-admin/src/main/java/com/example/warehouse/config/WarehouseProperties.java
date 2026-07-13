package com.example.warehouse.config;

import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.stereotype.Component;

@Component
@ConfigurationProperties(prefix = "warehouse")
public class WarehouseProperties {
    private final Mysql mysql = new Mysql();
    private final Actions actions = new Actions();
    private final Validation validation = new Validation();
    private final Auth auth = new Auth();

    public Mysql getMysql() { return mysql; }
    public Actions getActions() { return actions; }
    public Validation getValidation() { return validation; }
    public Auth getAuth() { return auth; }

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

    public static class Auth {
        private String adminUser = "admin";
        private String adminPass = "admin123";
        private String users = "";
        private String jwtSecret = "cdc-warehouse-platform-secret-key-2026-minimum-256-bit-length";
        private long jwtExpirationMs = 86400000L;
        private boolean cookieSecure;
        private String cookieSameSite = "Lax";

        public String getAdminUser() { return adminUser; }
        public void setAdminUser(String adminUser) { this.adminUser = adminUser; }
        public String getAdminPass() { return adminPass; }
        public void setAdminPass(String adminPass) { this.adminPass = adminPass; }
        public String getUsers() { return users; }
        public void setUsers(String users) { this.users = users; }
        public String getJwtSecret() { return jwtSecret; }
        public void setJwtSecret(String jwtSecret) { this.jwtSecret = jwtSecret; }
        public long getJwtExpirationMs() { return jwtExpirationMs; }
        public void setJwtExpirationMs(long jwtExpirationMs) { this.jwtExpirationMs = jwtExpirationMs; }
        public boolean isCookieSecure() { return cookieSecure; }
        public void setCookieSecure(boolean cookieSecure) { this.cookieSecure = cookieSecure; }
        public String getCookieSameSite() { return cookieSameSite; }
        public void setCookieSameSite(String cookieSameSite) { this.cookieSameSite = cookieSameSite; }
    }
}
