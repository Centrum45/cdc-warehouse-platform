package com.example.warehouse.controller;

import com.example.warehouse.model.LoginRequest;
import com.example.warehouse.security.JwtTokenProvider;
import java.util.HashMap;
import java.util.Map;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/auth")
public class AuthController {

    private final JwtTokenProvider tokenProvider;
    private final String adminUser;
    private final String adminPass;

    public AuthController(
            JwtTokenProvider tokenProvider,
            @Value("${warehouse.auth.admin-user:admin}") String adminUser,
            @Value("${warehouse.auth.admin-pass:admin123}") String adminPass) {
        this.tokenProvider = tokenProvider;
        this.adminUser = adminUser;
        this.adminPass = adminPass;
    }

    @PostMapping("/login")
    public ResponseEntity<?> login(@RequestBody LoginRequest request) {
        if (adminUser.equals(request.getUsername()) && adminPass.equals(request.getPassword())) {
            String token = tokenProvider.generateToken(request.getUsername());
            Map<String, String> body = new HashMap<>();
            body.put("token", token);
            body.put("username", request.getUsername());
            return ResponseEntity.ok(body);
        }
        Map<String, String> body = new HashMap<>();
        body.put("error", "Invalid credentials");
        return ResponseEntity.status(401).body(body);
    }
}
