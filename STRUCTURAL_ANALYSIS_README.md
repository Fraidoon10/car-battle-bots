# Car Battle Bot Frame - Structural Analysis

## Overview
This HTML webpage provides a comprehensive structural analysis tool for designing a car battle bot frame beam. The analysis includes load calculations, shear force and bending moment diagrams, stress analysis, and material selection recommendations.

## Features

### 🔧 Interactive Load Calculator
- Adjustable component loads (A, B, C, E, F)
- Dynamic loading factor for uneven terrain
- Real-time recalculation capability

### 📐 Visual Beam Diagram
- SVG-based beam representation
- Component load positions clearly marked
- Support locations indicated

### ⚖️ Structural Analysis
- Support reaction calculations
- Equilibrium equation verification
- Load summary with dynamic factors

### 📊 Force and Moment Diagrams
- Custom-drawn shear force diagram
- Bending moment diagram
- Interactive charts with proper scaling

### 🔬 Engineering Calculations
- Maximum bending moment determination
- Required section modulus calculation
- Deflection analysis with limits
- Safety factor verification

### 🛠️ Material Selection
- Steel grade recommendations (A36, A572, A514)
- Material property comparisons
- Suitability assessments

### 🛡️ Safety Analysis
- Multiple safety factors applied
- Battle bot specific requirements
- Dynamic loading considerations

## Usage

1. Open `structural_analysis.html` in a web browser
2. Adjust load values in the Interactive Load Calculator
3. Click "Recalculate Analysis" to update all calculations
4. Review results in each section:
   - Load summary and support reactions
   - Shear force and moment diagrams
   - Stress analysis results
   - Material recommendations
   - Safety factor assessment

## Technical Specifications

### Load Configuration
- **Component A**: 50 lb at 6" from left support
- **Component B**: 30 lb below Component A
- **Component C**: 14 lb distributed load across full beam
- **Component E**: 60 lb at 18" from left support
- **Component F**: 250 lb at 20" from left support
- **Beam Length**: 22 inches
- **Support Type**: Simply supported

### Design Criteria
- **Safety Factor**: 3.0 minimum (battle bot requirement)
- **Dynamic Factor**: 1.5 (uneven terrain)
- **Deflection Limit**: L/360
- **Steel Grades**: A36, A572 Grade 50, A514

### Calculations Include
- Static equilibrium analysis
- Shear force distribution
- Bending moment envelope
- Maximum stress determination
- Deflection estimation
- Material property verification

## Engineering Formulas Used

### Support Reactions
- ΣFy = 0: RA + RB - W_total = 0
- ΣM_A = 0: RB × L - Σ(moments about A) = 0

### Stress Analysis
- σ_max = M_max / S_required
- S_required = M_max / σ_allowable

### Deflection
- δ_max = (5WL⁴)/(384EI) for distributed loads
- Additional point load deflections calculated separately

## File Structure
- **HTML**: Complete self-contained webpage
- **CSS**: Embedded styling for professional appearance
- **JavaScript**: Interactive calculations and chart rendering
- **SVG**: Beam diagram visualization

## Browser Compatibility
- Modern browsers with HTML5 canvas support
- JavaScript enabled required
- No external dependencies

## Notes
- All calculations are based on standard structural engineering principles
- Simplified analysis suitable for preliminary design
- Professional engineering review recommended for final design
- Battle bot specific safety factors applied throughout