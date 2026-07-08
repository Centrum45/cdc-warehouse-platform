package com.example.warehouse.controller;

import com.example.warehouse.model.OnboardRequest;
import com.example.warehouse.model.TableMetadata;
import com.example.warehouse.service.DashboardService;
import com.example.warehouse.service.MetadataService;
import com.example.warehouse.service.OnboardingService;
import java.util.List;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.ModelAttribute;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.ResponseBody;

@Controller
public class MetadataController {
    private final MetadataService metadataService;
    private final DashboardService dashboardService;
    private final OnboardingService onboardingService;

    public MetadataController(MetadataService metadataService, DashboardService dashboardService, OnboardingService onboardingService) {
        this.metadataService = metadataService;
        this.dashboardService = dashboardService;
        this.onboardingService = onboardingService;
    }

    @GetMapping("/")
    public String index(Model model) {
        populateDashboard(model, defaultOnboardRequest());
        return "index";
    }

    @PostMapping("/")
    public String onboardFromDashboard(@ModelAttribute OnboardRequest request, Model model) {
        model.addAttribute("result", onboardingService.execute(request));
        populateDashboard(model, request);
        return "index";
    }

    @GetMapping("/api/dashboard")
    @ResponseBody
    public Object dashboard() {
        return dashboardService.snapshot(metadataService.listTables());
    }

    private void populateDashboard(Model model, OnboardRequest request) {
        List<TableMetadata> tables = metadataService.listTables();
        model.addAttribute("tables", tables);
        model.addAttribute("request", request);
        model.addAttribute("plan", onboardingService.buildPlan(request));
        model.addAttribute("dashboard", dashboardService.snapshot(tables));
    }

    private OnboardRequest defaultOnboardRequest() {
        OnboardRequest request = new OnboardRequest();
        request.setDatabaseName("basiccomment");
        request.setTableName("avatar_commentbatchsource");
        request.setDbaMetadataPath("metadata/dba/basiccomment.avatar_commentbatchsource.json");
        request.setPrimaryKeys("id");
        request.setVersionColumn("ver");
        request.setPartitionColumn("ctime");
        return request;
    }
}
