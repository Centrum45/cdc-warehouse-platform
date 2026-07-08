package com.example.warehouse.controller;

import com.example.warehouse.model.OnboardRequest;
import com.example.warehouse.service.OnboardingService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.ModelAttribute;
import org.springframework.web.bind.annotation.PostMapping;

@Controller
@Tag(name = "Onboarding", description = "MySQL-to-Hive table onboarding")
public class OnboardingController {
    private final OnboardingService onboardingService;

    public OnboardingController(OnboardingService onboardingService) {
        this.onboardingService = onboardingService;
    }

    @GetMapping("/onboarding")
    @Operation(summary = "Onboarding form page")
    public String onboarding(Model model) {
        OnboardRequest request = new OnboardRequest();
        request.setDatabaseName("basiccomment");
        request.setTableName("avatar_commentbatchsource");
        request.setDbaMetadataPath("metadata/dba/basiccomment.avatar_commentbatchsource.json");
        request.setPrimaryKeys("id");
        request.setVersionColumn("ver");
        request.setPartitionColumn("ctime");
        model.addAttribute("request", request);
        model.addAttribute("plan", onboardingService.buildPlan(request));
        return "onboarding";
    }

    @PostMapping("/onboarding")
    @Operation(summary = "Execute onboarding (MySQL boot + Hive DDL + scheduler pub)")
    public String execute(@ModelAttribute OnboardRequest request, Model model) {
        model.addAttribute("request", request);
        model.addAttribute("plan", onboardingService.buildPlan(request));
        model.addAttribute("result", onboardingService.execute(request));
        return "onboarding";
    }
}
