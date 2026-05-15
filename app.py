import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="Calc File Validator", page_icon="📊", layout="wide")

st.title("📊 Calc File Validator")
st.markdown("Upload a filled Calc File to check if its structure matches the Master Template.")

# -----------------------------------------
# CONFIGURATION
# -----------------------------------------
# Name of the master template file in your GitHub repository
MASTER_FILE_PATH = "master_template.xlsx" 

def validate_excel(master_path, target_file):
    report_lines = []
    has_errors = False
    
    try:
        master_xls = pd.ExcelFile(master_path)
    except FileNotFoundError:
        st.error(f"🚨 Master template '{master_path}' not found. Please ensure it is uploaded to your GitHub repository.")
        return None, True
        
    target_xls = pd.ExcelFile(target_file)
    
    master_sheets = master_xls.sheet_names
    target_sheets = target_xls.sheet_names
    
    report_lines.append("=== SHEET VALIDATION ===")
    
    missing_sheets = [s for s in master_sheets if s not in target_sheets]
    added_sheets = [s for s in target_sheets if s not in master_sheets]
    
    if missing_sheets:
        has_errors = True
        report_lines.append(f"❌ Missing Sheets: {', '.join(missing_sheets)}")
    if added_sheets:
        has_errors = True
        report_lines.append(f"⚠️ Added Sheets: {', '.join(added_sheets)}")
        
    if not missing_sheets and not added_sheets:
        report_lines.append("✅ All sheets match perfectly.")
        
    report_lines.append("\n=== COLUMN VALIDATION ===")
    
    common_sheets = [s for s in master_sheets if s in target_sheets]
    
    for sheet in common_sheets:
        report_lines.append(f"\n--- Checking Sheet: '{sheet}' ---")
        
        # Read only the first row (headers)
        df_master = pd.read_excel(master_path, sheet_name=sheet, nrows=0)
        df_target = pd.read_excel(target_file, sheet_name=sheet, nrows=0)
        
        master_cols = list(df_master.columns)
        target_cols = list(df_target.columns)
        
        missing_cols = [c for c in master_cols if c not in target_cols]
        added_cols = [c for c in target_cols if c not in master_cols]
        
        # Check sequence
        common_master = [c for c in master_cols if c in target_cols]
        common_target = [c for c in target_cols if c in master_cols]
        sequence_changed = common_master != common_target
        
        # Check placement of added columns
        if common_target:
            last_original_idx = max(target_cols.index(c) for c in common_target)
        else:
            last_original_idx = -1
            
        middle_added = [c for c in added_cols if target_cols.index(c) < last_original_idx]
        end_added = [c for c in added_cols if target_cols.index(c) > last_original_idx]
        
        sheet_errors = False
        
        if missing_cols:
            sheet_errors = True
            has_errors = True
            report_lines.append(f"❌ Missing Columns: {', '.join(missing_cols)}")
            
        if middle_added:
            sheet_errors = True
            has_errors = True
            report_lines.append(f"❌ Columns Inserted in Middle (Breaks DB): {', '.join(middle_added)}")
            
        if end_added:
            # Usually acceptable, but good to note
            report_lines.append(f"ℹ️ Columns Appended at End: {', '.join(end_added)}")
            
        if sequence_changed:
            sheet_errors = True
            has_errors = True
            report_lines.append(f"❌ Column Sequence Changed! Original order was modified.")
            
        if not sheet_errors and not end_added:
            report_lines.append("✅ Columns match perfectly.")
            
    return "\n".join(report_lines), has_errors

# -----------------------------------------
# UI LOGIC
# -----------------------------------------
uploaded_file = st.file_uploader("Upload an Excel file (.xlsx)", type=['xlsx'])

if uploaded_file is not None:
    st.info("File uploaded successfully. Validating...")
    
    report_text, errors_found = validate_excel(MASTER_FILE_PATH, uploaded_file)
    
    if report_text:
        st.subheader("Validation Report")
        
        # Display colored boxes in UI based on result
        if errors_found:
            st.error("🚨 Validation Failed! Issues were found in the structure.")
        else:
            st.success("✅ Validation Passed! Structure is intact.")
            
        # Display the text report in a code block for readability
        st.code(report_text, language='text')
        
        # Provide download button
        st.download_button(
            label="📥 Download Validation Report",
            data=report_text,
            file_name=f"Validation_Report_{uploaded_file.name}.txt",
            mime="text/plain"
        )
