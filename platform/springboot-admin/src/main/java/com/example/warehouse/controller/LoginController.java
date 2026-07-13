package com.example.warehouse.controller;

import com.example.warehouse.config.WarehouseProperties;
import com.example.warehouse.security.AuthUserService;
import com.example.warehouse.security.JwtAuthFilter;
import com.example.warehouse.security.JwtTokenProvider;
import javax.servlet.http.HttpServletResponse;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestParam;

@Controller
public class LoginController {
    private final AuthUserService authUserService;
    private final JwtTokenProvider tokenProvider;
    private final WarehouseProperties warehouseProperties;

    public LoginController(
            AuthUserService authUserService,
            JwtTokenProvider tokenProvider,
            WarehouseProperties warehouseProperties) {
        this.authUserService = authUserService;
        this.tokenProvider = tokenProvider;
        this.warehouseProperties = warehouseProperties;
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
        java.util.Optional<AuthUserService.AuthUser> user = authUserService.authenticate(username, password);
        if (!user.isPresent()) {
            return "redirect:/login?error=1";
        }
        addAuthCookie(response, tokenProvider.generateToken(username, user.get().getRole()), 24 * 60 * 60);
        return "redirect:/";
    }

    @GetMapping("/logout")
    public String logout(HttpServletResponse response) {
        addAuthCookie(response, "", 0);
        return "redirect:/login";
    }

    private void addAuthCookie(HttpServletResponse response, String value, int maxAgeSeconds) {
        StringBuilder header = new StringBuilder()
                .append(JwtAuthFilter.TOKEN_COOKIE).append("=").append(value)
                .append("; Path=/")
                .append("; Max-Age=").append(maxAgeSeconds)
                .append("; HttpOnly")
                .append("; SameSite=").append(warehouseProperties.getAuth().getCookieSameSite());
        if (warehouseProperties.getAuth().isCookieSecure()) {
            header.append("; Secure");
        }
        response.addHeader("Set-Cookie", header.toString());
    }
}
