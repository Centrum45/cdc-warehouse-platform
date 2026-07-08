package com.example.warehouse.controller;

import com.example.warehouse.model.OnboardRequest;
import com.example.warehouse.service.OnboardingService;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.ModelAttribute;
import org.springframework.web.bind.annotation.PostMapping;

@Controller
public class OnboardingController {
    private final OnboardingService onboardingService;

    public OnboardingController(OnboardingService onboardingService) {
        this.onboardingService = onboardingService;
    }

    @GetMapping("/onboarding")
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
    public String execute(@ModelAttribute OnboardRequest request, Model model) {
        model.addAttribute("request", request);
        model.addAttribute("plan", onboardingService.buildPlan(request));
        model.addAttribute("result", onboardingService.execute(request));
        return "onboarding";
    }
}
