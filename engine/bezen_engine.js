const fs = require('fs');
const path = require('path');

class BezenEngine {
    constructor() {
        this.patterns = [];
        this.loadPatterns();
    }

    loadPatterns() {
        try {
            const patternPath = path.join(__dirname, '..', 'data', 'patterns', 'pattern_map.json');
            const data = fs.readFileSync(patternPath, 'utf8');
            this.patterns = JSON.parse(data);
            console.log(`Loaded ${this.patterns.length} patterns`);
        } catch (error) {
            console.error('Error loading patterns:', error.message);
        }
    }

    findPatternByKeyword(keyword) {
        // Simple keyword matching - look for keyword in primary_feature or pattern_family
        return this.patterns.find(pattern =>
            pattern.primary_feature.includes(keyword) ||
            pattern.pattern_family.includes(keyword) ||
            pattern.emotion.includes(keyword) ||
            pattern.limiting_belief.includes(keyword)
        );
    }

    getAllPatterns() {
        return this.patterns;
    }

    getPatternById(id) {
        return this.patterns.find(pattern => pattern.pattern_id === id);
    }
}

module.exports = BezenEngine;