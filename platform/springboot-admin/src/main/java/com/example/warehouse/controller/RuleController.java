package com.example.warehouse.controller;

import com.example.warehouse.model.RuleRecord;
import com.example.warehouse.service.RuleService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.ModelAttribute;
import org.springframework.web.bind.annotation.PostMapping;

@Controller
@Tag(name = "Rules", description = "Sensitive data and quality rules")
public class RuleController {
    private final RuleService ruleService;

    public RuleController(RuleService ruleService) {
        this.ruleService = ruleService;
    }

    @GetMapping("/rules")
    @Operation(summary = "List sensitive/quality rules")
    public String rules(Model model) {
        RuleRecord rule = new RuleRecord();
        rule.setColumnName("mobile");
        rule.setAction("md5");
        model.addAttribute("rule", rule);
        model.addAttribute("rules", ruleService.listRules());
        return "rules";
    }

    @PostMapping("/rules/sensitive")
    @Operation(summary = "Save sensitive data rule")
    public String saveSensitive(@ModelAttribute RuleRecord rule, Model model) {
        ruleService.saveSensitive(rule);
        model.addAttribute("rule", rule);
        model.addAttribute("rules", ruleService.listRules());
        model.addAttribute("message", "sensitive rule saved");
        return "rules";
    }
}
