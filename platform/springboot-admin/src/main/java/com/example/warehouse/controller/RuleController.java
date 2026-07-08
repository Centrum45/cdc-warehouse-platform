package com.example.warehouse.controller;

import com.example.warehouse.model.RuleRecord;
import com.example.warehouse.service.RuleService;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.ModelAttribute;
import org.springframework.web.bind.annotation.PostMapping;

@Controller
public class RuleController {
    private final RuleService ruleService;

    public RuleController(RuleService ruleService) {
        this.ruleService = ruleService;
    }

    @GetMapping("/rules")
    public String rules(Model model) {
        RuleRecord rule = new RuleRecord();
        rule.setColumnName("mobile");
        rule.setAction("md5");
        model.addAttribute("rule", rule);
        model.addAttribute("rules", ruleService.listRules());
        return "rules";
    }

    @PostMapping("/rules/sensitive")
    public String saveSensitive(@ModelAttribute RuleRecord rule, Model model) {
        ruleService.saveSensitive(rule);
        model.addAttribute("rule", rule);
        model.addAttribute("rules", ruleService.listRules());
        model.addAttribute("message", "sensitive rule saved");
        return "rules";
    }
}
