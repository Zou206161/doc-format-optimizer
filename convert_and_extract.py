"""Convert .doc to .docx using Word COM, extract text and comments."""
import os, sys, shutil

src = r'c:\Users\lenpvp\.trae-cn\attachments\6a891b8548fd7c69dff220b2\ce842ffe-94ba-4336-b481-49a0724ff7b3_74ee3446-19f1-4905-a72f-3e3848e2d984_20221125092539.doc'

# Copy to working directory with simpler name
work_dir = os.path.dirname(os.path.abspath(__file__))
work_doc = os.path.join(work_dir, "user_uploaded.doc")
shutil.copy2(src, work_doc)

print(f"Source: {src}")
print(f"Working copy: {work_doc}")
print(f"Size: {os.path.getsize(work_doc)} bytes")

# Convert using Word COM
try:
    import win32com.client
    print("\n[1] Converting .doc to .docx via Word COM...")
    
    word = win32com.client.Dispatch("Word.Application")
    word.Visible = False
    word.DisplayAlerts = False
    
    docx_path = os.path.join(work_dir, "user_uploaded.docx")
    
    # Open the .doc file
    doc = word.Documents.Open(work_doc, ReadOnly=True)
    
    # Save as .docx (format 16 = wdFormatXMLDocument)
    doc.SaveAs2(docx_path, FileFormat=16)
    print(f"  Converted: {docx_path}")
    print(f"  Size: {os.path.getsize(docx_path)} bytes")
    
    # Extract comments/annotations
    print("\n[2] Extracting comments/annotations...")
    comments = doc.Comments
    print(f"  Comment count: {comments.Count}")
    for i in range(1, comments.Count + 1):
        c = comments(i)
        print(f"  Comment {i}:")
        print(f"    Author: {c.Author}")
        print(f"    Text: {c.Range.Text[:80]}...")
        print(f"    Scope: {c.Scope.Text[:60]}...")
    
    # Extract revision marks (track changes)
    print("\n[3] Checking for revision marks...")
    revisions = doc.Revisions
    print(f"  Revision count: {revisions.Count}")
    
    # Extract red colored text (formatting annotations)
    print("\n[4] Scanning for red-colored text (formatting hints)...")
    red_texts = []
    for para_idx in range(1, doc.Paragraphs.Count + 1):
        para = doc.Paragraphs(para_idx)
        for char_idx in range(1, para.Range.Characters.Count + 1):
            char = para.Range.Characters(char_idx)
            try:
                color = char.Font.Color
                # Red = 255 (0xFF0000 in RGB), or common red variants
                if color == 255 or color == 128:
                    # Collect the full word/phrase
                    start = char.Start
                    # Find the extent of red text
                    end = start
                    while end < para.Range.End:
                        temp_char = doc.Range(Start=end, End=end+1)
                        try:
                            if temp_char.Font.Color == color:
                                end += 1
                            else:
                                break
                        except:
                            break
                    red_text = doc.Range(Start=start, End=end).Text
                    if red_text.strip() and len(red_text.strip()) > 1:
                        red_texts.append({
                            "para": para_idx,
                            "text": red_text.strip(),
                            "color": color,
                        })
                        # Skip past this red section
                        break  # Move to next paragraph to avoid duplicates
            except:
                continue
    
    print(f"  Red text segments found: {len(red_texts)}")
    for rt in red_texts:
        print(f"    Para {rt['para']}: [{rt['text'][:80]}] (color={rt['color']})")
    
    doc.Close(False)
    word.Quit()
    
    # Now parse the .docx with our system
    print("\n[5] Parsing converted .docx with our parser...")
    sys.path.insert(0, work_dir)
    from src.modules.parser import parse_document
    
    doc_obj = parse_document(docx_path)
    print(f"  Paragraphs: {len(doc_obj.paragraphs)}")
    print(f"  Tables: {len(doc_obj.tables)}")
    print(f"  Page: {doc_obj.page_width}x{doc_obj.page_height}pt")
    print(f"  Margins: T={doc_obj.margin_top} B={doc_obj.margin_bottom} L={doc_obj.margin_left} R={doc_obj.margin_right}pt")
    
    print(f"\n[6] Paragraph contents (first 30):")
    for i, p in enumerate(doc_obj.paragraphs[:30]):
        font_name = p.font.font_name_east_asia or p.font.font_name or "?"
        size = p.font.font_size or "?"
        color = p.font.color or ""
        print(f"  [{i}] style={p.style_name:20s} font={font_name:8s} size={str(size):5s} color={str(color):10s} | {p.text[:50]}")
    
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
    try:
        word.Quit()
    except:
        pass
