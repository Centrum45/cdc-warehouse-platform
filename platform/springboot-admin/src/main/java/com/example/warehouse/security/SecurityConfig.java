package com.example.warehouse.security;

import com.example.warehouse.config.WarehouseProperties;
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
                .antMatchers("/api/dashboard").permitAll()
                .antMatchers("/swagger-ui/**", "/v3/api-docs/**").permitAll()
                .antMatchers("/", "/css/**", "/js/**", "/webjars/**").permitAll();

        if (warehouseProperties.getActions().isPublicEnabled()) {
            http.authorizeRequests().antMatchers("/api/actions/**").permitAll();
        }

        http.authorizeRequests()
            // Protected endpoints
            .antMatchers("/tasks/**", "/onboarding/**", "/replay/**",
                         "/monitors/**", "/rules/**", "/api/**").authenticated()
            .anyRequest().authenticated()
            .and()
            .addFilterBefore(
            new JwtAuthFilter(jwtTokenProvider),
            UsernamePasswordAuthenticationFilter.class);

        return http.build();
    }
}
