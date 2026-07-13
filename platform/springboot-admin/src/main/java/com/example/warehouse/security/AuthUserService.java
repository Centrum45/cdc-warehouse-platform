package com.example.warehouse.security;

import com.example.warehouse.config.WarehouseProperties;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Locale;
import java.util.Optional;
import org.springframework.stereotype.Service;

@Service
public class AuthUserService {
    public static final String ROLE_ADMIN = "ADMIN";
    public static final String ROLE_OPERATOR = "OPERATOR";
    public static final String ROLE_VIEWER = "VIEWER";

    private final WarehouseProperties warehouseProperties;

    public AuthUserService(WarehouseProperties warehouseProperties) {
        this.warehouseProperties = warehouseProperties;
    }

    public Optional<AuthUser> authenticate(String username, String password) {
        return users().stream()
                .filter(user -> user.getUsername().equals(username) && user.getPassword().equals(password))
                .findFirst();
    }

    public List<AuthUser> users() {
        String configuredUsers = warehouseProperties.getAuth().getUsers();
        if (configuredUsers == null || configuredUsers.trim().isEmpty()) {
            return Collections.singletonList(new AuthUser(
                    warehouseProperties.getAuth().getAdminUser(),
                    warehouseProperties.getAuth().getAdminPass(),
                    ROLE_ADMIN));
        }
        List<AuthUser> result = new ArrayList<>();
        for (String entry : configuredUsers.split(",")) {
            String trimmed = entry.trim();
            if (trimmed.isEmpty()) {
                continue;
            }
            String[] parts = trimmed.split(":", 3);
            if (parts.length != 3) {
                continue;
            }
            result.add(new AuthUser(parts[0], parts[1], normalizeRole(parts[2])));
        }
        return result;
    }

    private String normalizeRole(String role) {
        String normalized = role == null ? "" : role.trim().toUpperCase(Locale.ROOT);
        if (ROLE_OPERATOR.equals(normalized) || ROLE_VIEWER.equals(normalized)) {
            return normalized;
        }
        return ROLE_ADMIN;
    }

    public static class AuthUser {
        private final String username;
        private final String password;
        private final String role;

        public AuthUser(String username, String password, String role) {
            this.username = username;
            this.password = password;
            this.role = role;
        }

        public String getUsername() { return username; }
        public String getPassword() { return password; }
        public String getRole() { return role; }
    }
}
