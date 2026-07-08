package com.example.warehouse.service;

import com.example.warehouse.model.RuleRecord;
import com.example.warehouse.repository.RuleRepository;
import java.util.Arrays;
import java.util.List;
import org.springframework.stereotype.Service;

@Service
public class RuleService {
    private final RuleRepository ruleRepository;

    public RuleService(RuleRepository ruleRepository) {
        this.ruleRepository = ruleRepository;
    }

    public List<RuleRecord> listRules() {
        List<RuleRecord> rules = ruleRepository.findAll();
        if (!rules.isEmpty()) {
            return rules;
        }
        RuleRecord rule = new RuleRecord();
        rule.setRuleCategory("sensitive");
        rule.setColumnName("mobile");
        rule.setAction("md5");
        return Arrays.asList(rule);
    }

    public void saveSensitive(RuleRecord rule) {
        ruleRepository.saveSensitive(rule);
    }
}
