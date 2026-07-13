package com.example.warehouse.controller;

import com.example.warehouse.model.LoginRequest;
import com.example.warehouse.security.AuthUserService;
import com.example.warehouse.security.JwtTokenProvider;
import java.util.HashMap;
import java.util.Map;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/auth")
public class AuthController {

    private final JwtTokenProvider tokenProvider;
    private final AuthUserService authUserService;

    public AuthController(
            JwtTokenProvider tokenProvider,
            AuthUserService authUserService) {
        this.tokenProvider = tokenProvider;
        this.authUserService = authUserService;
    }

    @PostMapping("/login")
    public ResponseEntity<?> login(@RequestBody LoginRequest request) {
        java.util.Optional<AuthUserService.AuthUser> user =
                authUserService.authenticate(request.getUsername(), request.getPassword());
        if (user.isPresent()) {
            String token = tokenProvider.generateToken(request.getUsername(), user.get().getRole());
            Map<String, String> body = new HashMap<>();
            body.put("token", token);
            body.put("username", request.getUsername());
            body.put("role", user.get().getRole());
            return ResponseEntity.ok(body);
        }
        Map<String, String> body = new HashMap<>();
        body.put("error", "Invalid credentials");
        return ResponseEntity.status(401).body(body);
    }
}
