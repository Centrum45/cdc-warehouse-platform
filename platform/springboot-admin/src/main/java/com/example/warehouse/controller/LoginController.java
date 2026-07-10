package com.example.warehouse.controller;

import com.example.warehouse.security.JwtAuthFilter;
import com.example.warehouse.security.JwtTokenProvider;
import javax.servlet.http.Cookie;
import javax.servlet.http.HttpServletResponse;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestParam;

@Controller
public class LoginController {
    private final JwtTokenProvider tokenProvider;
    private final String adminUser;
    private final String adminPass;

    public LoginController(
            JwtTokenProvider tokenProvider,
            @Value("${warehouse.auth.admin-user:admin}") String adminUser,
            @Value("${warehouse.auth.admin-pass:admin123}") String adminPass) {
        this.tokenProvider = tokenProvider;
        this.adminUser = adminUser;
        this.adminPass = adminPass;
    }

    @GetMapping("/login")
    public String login(Model model, @RequestParam(value = "error", required = false) String error) {
        if (error != null) {
            model.addAttribute("error", "Invalid username or password");
        }
        return "login";
    }

    @PostMapping("/login")
    public String doLogin(
            @RequestParam String username,
            @RequestParam String password,
            HttpServletResponse response) {
        if (!adminUser.equals(username) || !adminPass.equals(password)) {
            return "redirect:/login?error=1";
        }
        Cookie cookie = new Cookie(JwtAuthFilter.TOKEN_COOKIE, tokenProvider.generateToken(username));
        cookie.setHttpOnly(true);
        cookie.setPath("/");
        cookie.setMaxAge(24 * 60 * 60);
        response.addCookie(cookie);
        return "redirect:/";
    }

    @GetMapping("/logout")
    public String logout(HttpServletResponse response) {
        Cookie cookie = new Cookie(JwtAuthFilter.TOKEN_COOKIE, "");
        cookie.setHttpOnly(true);
        cookie.setPath("/");
        cookie.setMaxAge(0);
        response.addCookie(cookie);
        return "redirect:/login";
    }
}
