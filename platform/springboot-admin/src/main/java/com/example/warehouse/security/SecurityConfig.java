package com.example.warehouse.security;

import com.example.warehouse.config.WarehouseProperties;
import javax.servlet.http.HttpServletResponse;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.config.http.SessionCreationPolicy;
import org.springframework.security.web.SecurityFilterChain;
import org.springframework.security.web.authentication.UsernamePasswordAuthenticationFilter;

@Configuration
@EnableWebSecurity
public class SecurityConfig {

    private final JwtTokenProvider jwtTokenProvider;
    private final WarehouseProperties warehouseProperties;

    public SecurityConfig(JwtTokenProvider jwtTokenProvider, WarehouseProperties warehouseProperties) {
        this.jwtTokenProvider = jwtTokenProvider;
        this.warehouseProperties = warehouseProperties;
    }

    @Bean
    public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
        http
            .csrf().disable()
            .sessionManagement().sessionCreationPolicy(SessionCreationPolicy.STATELESS)
            .and()
            .authorizeRequests()
                // Public endpoints
                .antMatchers("/api/auth/**").permitAll()
                .antMatchers("/login", "/logout", "/admin.css", "/css/**", "/js/**", "/webjars/**").permitAll();

        if (warehouseProperties.getActions().isPublicEnabled()) {
            http.authorizeRequests()
                .antMatchers("/", "/swagger-ui/**", "/v3/api-docs/**").permitAll()
                .antMatchers("/api/dashboard", "/api/actions/**", "/api/hive/**", "/api/realtime/**").permitAll()
                .antMatchers("/api/tasks/**", "/api/metadata/**", "/api/table-ops/**").permitAll()
                .antMatchers("/tasks/**", "/onboarding/**", "/replay/**",
                    "/monitors/**", "/rules/**", "/logs/**", "/realtime/**", "/table-ops/**").permitAll()
                .anyRequest().authenticated();
        } else {
            http.authorizeRequests()
                .antMatchers("/", "/swagger-ui/**", "/v3/api-docs/**").authenticated()
                .antMatchers("/api/**").authenticated()
                .antMatchers("/tasks/**", "/onboarding/**", "/replay/**",
                    "/monitors/**", "/rules/**", "/logs/**", "/realtime/**", "/table-ops/**").authenticated()
                .anyRequest().authenticated();
        }

        http.exceptionHandling()
                .authenticationEntryPoint((request, response, authException) -> {
                    if (request.getRequestURI().startsWith("/api/")) {
                        response.sendError(HttpServletResponse.SC_UNAUTHORIZED);
                    } else {
                        response.sendRedirect("/login");
                    }
                })
            .and()
            .addFilterBefore(
            new JwtAuthFilter(jwtTokenProvider),
            UsernamePasswordAuthenticationFilter.class);

        return http.build();
    }
}
