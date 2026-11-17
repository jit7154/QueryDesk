#!/usr/bin/env python3
"""Generate realistic synthetic RetailFlow business documents in PDF and DOCX formats."""

from pathlib import Path
import docx
from docx.shared import Inches, Pt, RGBColor
import pymupdf

DOCS_DIR = Path(__file__).resolve().parent.parent / "documents"

# Document specifications grounded with real seller IDs from PostgreSQL
DOCUMENTS_SPEC = [
    {
        "filename": "Supplier_Contract_Apex_6560211a19b4",
        "title": "Master Supplier Agreement - Apex Logistics & Retail Solutions",
        "seller_id": "6560211a19b47992c3666cc44a7e94c0",
        "category": "Supplier Contract",
        "pages": [
            [
                ("Section 1.0: Parties and Purpose",
                 "This Master Supplier Agreement ('Agreement') is entered into between RetailFlow Inc. ('RetailFlow') and Apex Logistics & Retail Solutions ('Supplier', Seller ID: 6560211a19b47992c3666cc44a7e94c0), registered in Sao Paulo, SP. The Supplier agrees to supply goods across electronics, home appliances, and accessories categories under the terms detailed herein."),
                ("Section 2.0: Order Fulfillment and Dispatch SLAs",
                 "The Supplier agrees to process, pack, and release all customer purchase orders to the designated logistics carrier within 24 hours of order notification. Any delay exceeding 24 hours requires immediate notification to RetailFlow Vendor Management."),
                ("Section 3.0: Pricing and Freight Cost Allocation",
                 "Wholesale unit pricing is locked for 12 months from contract execution. Standard freight subsidy of 8% is credited monthly against validated shipping manifests.")
            ],
            [
                ("Section 7.2: Late Delivery Penalties",
                 "In the event of unexcused shipment delays where actual customer delivery exceeds the carrier estimated delivery date by three (3) or more calendar days, Supplier shall incur a mandatory penalty of 4% of the total gross order value per week of delay, capped at a maximum of 25% of the delayed order total. RetailFlow reserves the right to deduct accrued late delivery penalties directly from Supplier's monthly disbursement accounts."),
                ("Section 8.0: Quality Control and Maximum Defect Threshold",
                 "Supplier must maintain a return rate attributable to product defect or damage below 1.5% of total units shipped per calendar quarter. Failure to maintain this threshold may trigger a formal quality audit and temporary account suspension.")
            ],
            [
                ("Section 9.0: Warranty and Defective Merchandise Replacement",
                 "Supplier warrants that all products delivered shall be free from manufacturing defects for a minimum period of twelve (12) months from customer delivery date. Defective items returned within this window shall be reimbursed at 100% invoice price."),
                ("Section 10.0: Term, Termination, and Governing Law",
                 "This Agreement is valid for two (2) years. This contract is governed by the laws of Brazil, with exclusive jurisdiction in the courts of Sao Paulo, SP.")
            ]
        ]
    },
    {
        "filename": "Supplier_Contract_Vanguard_4a3ca9315b74",
        "title": "Supplier Agreement - Vanguard Home & Textiles",
        "seller_id": "4a3ca9315b744ce9f8e9374361493884",
        "category": "Supplier Contract",
        "pages": [
            [
                ("Section 1.0: Scope of Supply Agreement",
                 "This Agreement governs the relationship between RetailFlow and Vanguard Home & Textiles ('Supplier', Seller ID: 4a3ca9315b744ce9f8e9374361493884), operating out of Ibitinga, SP. Supplier provides bed, bath, and interior home textiles for marketplace catalog distribution."),
                ("Section 2.5: Packaging and Barcode Compliance",
                 "All textiles must be sealed in 100% recyclable polybags with legible EAN-13 barcodes compliant with RetailFlow automated sortation center specifications.")
            ],
            [
                ("Section 6.1: Late Delivery and Liquidated Damages",
                 "Timely fulfillment is of the essence. For any shipment where delivery to the carrier or customer exceeds the contracted shipping limit date by more than 48 hours, liquidated damages of 6% of the order line-item value per calendar week shall be assessed. If the delay extends past seven (7) business days, RetailFlow reserves the right to cancel the order and reallocate order items without liability."),
                ("Section 7.0: Carrier Coordination and Dispatch Documentation",
                 "Supplier must upload valid carrier tracking numbers into the RetailFlow EDI gateway within two hours of shipment handoff.")
            ],
            [
                ("Section 8.3: Customer Returns for Misdescribed Textiles",
                 "Textiles returned due to incorrect thread count, mismatched color swatches, or dimensional inaccuracies shall be fully charged back to the Supplier, including two-way shipping fees."),
                ("Section 11.0: Dispute Resolution and Severability",
                 "Disputes arising under this contract shall be submitted to binding arbitration under the rules of the American Arbitration Association, held in Sao Paulo, SP.")
            ]
        ]
    },
    {
        "filename": "Supplier_Contract_Horizon_1f50f920176f",
        "title": "Vendor Partnership Contract - Horizon Electronics Global",
        "seller_id": "1f50f920176fa81dab994f9023523100",
        "category": "Supplier Contract",
        "pages": [
            [
                ("Section 1.0: Executive Partnership Framework",
                 "Partnership agreement between RetailFlow and Horizon Electronics Global ('Supplier', Seller ID: 1f50f920176fa81dab994f9023523100), located in Sao Jose do Rio Preto, SP. Supplier provides consumer electronics, smart audio gear, and peripheral hardware."),
                ("Section 3.1: Inventory Level Commitments",
                 "Supplier agrees to maintain a safety buffer inventory of at least 300 units per active SKU at all times to prevent backorders during peak sales campaigns.")
            ],
            [
                ("Section 5.4: Late Delivery Penalties and Restocking Surcharges",
                 "Delays in fulfilling confirmed orders past the designated shipping limit date will incur an automatic 8% deduction from the gross invoice total for unexcused delays beyond five (5) business days past the scheduled delivery estimate. Continued delays exceeding ten (10) days permit RetailFlow to cancel the order with full compensation."),
                ("Section 6.2: Serial Number Tracking",
                 "Every electronic unit must have its unique serial number scanned and transmitted via API before warehouse intake.")
            ],
            [
                ("Section 8.0: Product Safety and Regulatory Standards",
                 "Supplier certifies full compliance with national electrical safety standards (ANATEL certification). Any fines resulting from non-certified hardware shall be borne exclusively by Supplier."),
                ("Section 12.0: Term and Confidentiality",
                 "This contract is effective for 36 months and contains mutual non-disclosure obligations.")
            ]
        ]
    },
    {
        "filename": "Supplier_Contract_Nova_cc419e0650a3",
        "title": "Industrial Supply Agreement - Nova Industrial Supply Ltd",
        "seller_id": "cc419e0650a3c5ba77189a1882b7556a",
        "category": "Supplier Contract",
        "pages": [
            [
                ("Section 1.0: Master Agreement Terms",
                 "This Agreement is between RetailFlow and Nova Industrial Supply Ltd ('Supplier', Seller ID: cc419e0650a3c5ba77189a1882b7556a), located in Santo Andre, SP. Supplier provides industrial tools, automotive components, and heavy hardware."),
                ("Section 2.0: Freight and Heavy Cargo Protocols",
                 "Products exceeding 15kg in weight must be palletized and secured in accordance with RetailFlow Freight Guide Revision 4.")
            ],
            [
                ("Section 7.2: Late Delivery Penalties Clause",
                 "For any hardware shipment where transit delivery fails to meet the carrier estimated delivery date, a flat administrative late fee of R$ 50.00 per delayed order plus an additional 3% daily recurring charge on the order total shall be applied for every calendar day the delivery is delayed beyond 48 hours past the estimate."),
                ("Section 8.0: Pallet Damage and Freight Claim Deductions",
                 "In transit pallet damage caused by insufficient packaging will result in a 100% debit of the damaged items against Supplier receivables.")
            ],
            [
                ("Section 10.0: Termination for Non-Performance",
                 "RetailFlow may terminate this agreement immediately if Supplier incurs late delivery penalties on more than 5% of monthly purchase orders."),
                ("Section 11.0: Signatures and Authority",
                 "Duly authorized representatives execute this contract as of January 15, 2024.")
            ]
        ]
    },
    {
        "filename": "Supplier_Contract_Starlight_da8622b14eb1",
        "title": "Merchant Supply Agreement - Starlight Consumer Goods",
        "seller_id": "da8622b14eb17ae2831f4ac5b9dab84a",
        "category": "Supplier Contract",
        "pages": [
            [
                ("Section 1.0: General Terms of Supply",
                 "This Agreement is executed between RetailFlow and Starlight Consumer Goods ('Supplier', Seller ID: da8622b14eb17ae2831f4ac5b9dab84a), operating in Piracicaba, SP. Supplier supplies beauty, personal hygiene, and baby care items."),
                ("Section 2.2: Expiration Date Requirements",
                 "No consumable or topical product may be shipped with less than eighteen (18) months remaining until manufacturer expiration.")
            ],
            [
                ("Section 4.5: Late Delivery Remedies and Chargebacks",
                 "When verified carrier delivery exceeds the promised customer estimated delivery date by more than four (4) days due to Supplier dispatch delays, RetailFlow shall execute an immediate 5% freight subsidy deduction and assess a 5% order penalty against the Supplier's monthly settlement balance."),
                ("Section 6.0: Temperature-Controlled Transport Standards",
                 "Supplier must adhere to verified climate-controlled transit standards for all cosmetic emulsions during summer operational cycles.")
            ],
            [
                ("Section 8.2: Counterfeit and Brand Protection Guarantee",
                 "Supplier guarantees that all goods supplied are authentic and directly sourced from authorized brand distributors. Infringement triggers immediate contract termination and liquidated damages of R$ 100,000."),
                ("Section 10.0: Execution and Jurisdiction",
                 "Executed in Piracicaba, SP on February 1, 2024.")
            ]
        ]
    },
    {
        "filename": "RetailFlow_Refund_and_Returns_Policy",
        "title": "RetailFlow Global Refund and Returns Policy",
        "seller_id": None,
        "category": "Corporate Policy",
        "pages": [
            [
                ("Section 1.0: General Return Eligibility Window",
                 "RetailFlow customers are entitled to initiate a return for any standard physical item within thirty (30) calendar days from the date of confirmed carrier delivery. Items must be in original condition with intact manufacturer packaging, accessories, and user manuals."),
                ("Section 2.0: Return Authorization and RMA Procedures",
                 "To initiate a return, customers must submit a request through the RetailFlow portal to receive a prepaid Return Merchandise Authorization (RMA) shipping label. Customers must drop off the parcel at an authorized carrier depot within seven (7) business days of RMA issuance.")
            ],
            [
                ("Section 4.1: Damaged and Defective Products",
                 "If an item arrives damaged in transit, defective, or missing components, the customer is entitled to an immediate 100% full refund or complimentary replacement, including all original shipping and freight charges. Customers must report transit damage within seven (7) days of delivery and provide photographic evidence of the damaged packaging and product via the customer support chat or ticket system. Once photos are verified by customer care, refunds are processed within forty-eight (48) hours back to the original payment method without requiring the customer to return severely broken or hazardous items."),
                ("Section 5.0: Non-Returnable and Final Sale Categories",
                 "Customized personalized items, opened software, intimate apparel, and gift cards are strictly non-returnable unless arrived damaged or defective under Section 4.1.")
            ]
        ]
    },
    {
        "filename": "Q3_RetailFlow_Financial_Summary",
        "title": "RetailFlow Q3 Executive Financial Summary and Operational Report",
        "seller_id": None,
        "category": "Financial Report",
        "pages": [
            [
                ("Section 1.1: Executive Revenue and Gross Merchandise Value",
                 "During Q3, RetailFlow processed over 99,000 fulfilled customer orders across Brazilian logistics corridors, generating total Gross Merchandise Value (GMV) of R$ 15.8 million, representing an 11.4% year-over-year increase in top-line transaction volume. Operating margin stood at 18.2%."),
                ("Section 2.1: Logistics and Freight Cost Dynamics",
                 "Logistics expenditures represented 14.2% of total net revenue. Urban last-mile delivery costs in Sao Paulo and Rio de Janeiro dropped by 4.5% due to enhanced micro-hub sorting efficiency.")
            ],
            [
                ("Section 3.2: Supplier Late Delivery Penalties and Recoveries",
                 "In Q3, RetailFlow recovered R$ 412,850 in contractual liquidated damages and late delivery penalty deductions across defaulting marketplace suppliers. Enforcing supplier penalty clauses (such as Section 7.2) reduced transit delay frequencies from 6.8% to 4.1% of all dispatched orders."),
                ("Section 4.0: Q4 Capital Expenditures and Forward Projections",
                 "Projected Q4 investment prioritizes expansion of automated inventory sortation hubs in Minas Gerais and Parana to support holiday sales surges.")
            ]
        ]
    },
    {
        "filename": "Procurement_and_Vendor_Policy",
        "title": "RetailFlow Procurement and Vendor Management Policy",
        "seller_id": None,
        "category": "Corporate Policy",
        "pages": [
            [
                ("Section 1.0: Purpose and Scope",
                 "This policy defines mandatory standards for vendor onboarding, ongoing performance monitoring, and procurement ethics across all business units of RetailFlow Inc."),
                ("Section 2.1: Vendor Onboarding and Vetting Criteria",
                 "All prospective commercial suppliers must undergo financial stability vetting, tax compliance verification (CNPJ registration), and environmental impact screening prior to catalog activation.")
            ],
            [
                ("Section 3.4: Supplier SLA Benchmarks and Default Penalties",
                 "Vendors must achieve an on-time dispatch rate of at least 96.5% and a customer delivery success rate of 98.0%. When a supplier repeatedly breaches SLA targets, procurement managers are required to enforce contractual late fees (e.g. 4% to 8% weekly penalty) and may down-rank merchant listings in marketplace search algorithms."),
                ("Section 5.0: Ethical Conduct and Anti-Bribery Compliance",
                 "RetailFlow prohibits the offering, giving, soliciting, or acceptance of any kickback, bribe, or inappropriate corporate gift exceeding R$ 150 in value.")
            ]
        ]
    },
    {
        "filename": "Warehouse_Operations_Report_2024",
        "title": "RetailFlow Fulfillment Center Annual Operations Report",
        "seller_id": None,
        "category": "Operations Report",
        "pages": [
            [
                ("Section 1.2: Fulfillment Hub Throughput and Regional Metrics",
                 "RetailFlow operated five major regional fulfillment hubs in 2024: Sao Paulo Central (SP01), Campinas Distribution (SP02), Rio de Janeiro Hub (RJ01), Belo Horizonte Center (MG01), and Curitiba Hub (PR01). Total annual sortation capacity exceeded 1.2 million parcels."),
                ("Section 2.4: Carrier Bottlenecks and Transit Delay Analysis",
                 "Interstate shipments between Southeastern hubs and Northern states exhibited average transit delays of 4.2 business days compared to original estimates, primarily driven by road infrastructure bottlenecks. Vendor delayed dispatches accounted for 31% of total delivery complaints.")
            ],
            [
                ("Section 3.1: Inventory Turn Rates and Stockout Mitigation",
                 "Top moving categories—health & beauty, bed & bath textiles, and computers accessories—maintained an average turnover velocity of 21.4 days. Automated restocking alerts mitigated potential stockouts by 42%."),
                ("Section 4.3: Automation and Robotics Integration",
                 "Deployment of optical sorting arms at SP01 decreased parcel handling errors by 65% and reduced parcel damage during sortation to 0.08%.")
            ]
        ]
    },
    {
        "filename": "RetailFlow_Regulatory_Compliance_Policy",
        "title": "Corporate Regulatory Compliance and Consumer Protection Policy",
        "seller_id": None,
        "category": "Compliance Policy",
        "pages": [
            [
                ("Section 1.0: Consumer Protection Code (CDC) Adherence",
                 "RetailFlow adheres strictly to Brazilian Consumer Defense Code (Law No. 8,078). Under Article 49 ('Right of Regret'), consumers are guaranteed the statutory right to cancel any e-commerce contract within seven (7) days of delivery without penalty or explanation."),
                ("Section 2.0: Pricing Transparency and Invoice Accuracy",
                 "All listed prices must display the total price including all applicable sales taxes (ICMS, PIS, COFINS) and freight charges before final checkout confirmation.")
            ],
            [
                ("Section 3.2: Data Privacy, LGPD, and Payment Card Standards",
                 "In full compliance with Lei Geral de Protecao de Dados (LGPD) and PCI-DSS Level 1, customer personal identifying information (PII) and payment credentials are encrypted in transit and at rest using AES-256 encryption. Access to customer billing tables is restricted to audited backend services."),
                ("Section 4.0: Product Safety and Environmental Regulations",
                 "RetailFlow strictly prohibits the sale of hazardous, counterfeit, or recalled consumer merchandise. Vendors must upload valid safety certificates prior to listing.")
            ]
        ]
    },
    {
        "filename": "Customer_Support_SOP_Order_Escalations",
        "title": "Customer Support Standard Operating Procedure - Order Escalations",
        "seller_id": None,
        "category": "Standard Operating Procedure",
        "pages": [
            [
                ("Section 1.0: SOP Purpose and Target Audiences",
                 "This SOP establishes standardized resolution workflows for frontline customer support specialists handling order delays, carrier exceptions, damage reports, and merchant disputes."),
                ("Section 2.1: Tier-1 and Tier-2 Escalation Workflows",
                 "Routine inquiries (order tracking, password resets) are resolved by Tier-1 chat agents within 5 minutes. Inquiries involving transit delays exceeding 5 days, lost parcels, or supplier disputes are immediately routed to Tier-2 senior specialists.")
            ],
            [
                ("Section 3.5: Delayed Order Compensation Matrix",
                 "When a customer contacts support regarding an order delayed beyond the estimated delivery date: (a) If delay is 3 to 5 business days: Issue an immediate apology message and a R$ 25.00 store credit voucher. (b) If delay exceeds 5 business days: Offer customer choice between immediate 100% freight charge refund or complete order cancellation with 100% refund. The cost of delay vouchers is charged back to the responsible supplier."),
                ("Section 4.2: Damaged Freight Incident Logging and Claims",
                 "Support specialists must log all damaged freight reports with photographic evidence under incident code DMG-101 within 2 hours of customer contact.")
            ]
        ]
    }
]


def generate_pdf(doc_spec: dict, output_path: Path) -> None:
    """Generate a multi-page PDF document with headers, sections, and page numbers."""
    pdf = pymupdf.open()
    total_pages = len(doc_spec["pages"])
    
    for page_num, sections in enumerate(doc_spec["pages"], start=1):
        page = pdf.new_page(width=595, height=842)  # A4: 595 x 842 points
        
        # Header banner
        page.draw_rect(pymupdf.Rect(40, 30, 555, 65), color=None, fill=(0.95, 0.96, 0.98))
        page.insert_text(
            pymupdf.Point(50, 48),
            "RETAILFLOW CORP  |  INTERNAL BUSINESS DOCUMENT",
            fontsize=8,
            fontname="helv",
            color=(0.3, 0.35, 0.45)
        )
        page.insert_text(
            pymupdf.Point(50, 60),
            doc_spec["title"][:75],
            fontsize=10,
            fontname="hebo",
            color=(0.1, 0.12, 0.2)
        )
        
        # Body text layout
        y_cursor = 90
        for heading, body in sections:
            # Section Heading
            page.insert_text(
                pymupdf.Point(40, y_cursor),
                heading,
                fontsize=11,
                fontname="hebo",
                color=(0.12, 0.2, 0.35)
            )
            y_cursor += 16
            
            # Section Body text box
            rect = pymupdf.Rect(40, y_cursor, 555, y_cursor + 180)
            rc = page.insert_textbox(
                rect,
                body,
                fontsize=9.5,
                fontname="helv",
                color=(0.15, 0.15, 0.18),
                lineheight=1.35
            )
            y_cursor += 120
            page.draw_line(pymupdf.Point(40, y_cursor), pymupdf.Point(555, y_cursor), color=(0.88, 0.9, 0.92), width=0.5)
            y_cursor += 25
            
        # Footer
        footer_line_y = 800
        page.draw_line(pymupdf.Point(40, footer_line_y), pymupdf.Point(555, footer_line_y), color=(0.8, 0.82, 0.85), width=0.5)
        page.insert_text(
            pymupdf.Point(40, 815),
            f"Doc ID: {doc_spec['filename']}  |  Classification: Confidential",
            fontsize=8,
            fontname="helv",
            color=(0.4, 0.45, 0.5)
        )
        page.insert_text(
            pymupdf.Point(480, 815),
            f"Page {page_num} of {total_pages}",
            fontsize=8,
            fontname="helv",
            color=(0.4, 0.45, 0.5)
        )
        
    pdf.save(str(output_path))
    pdf.close()


def generate_docx(doc_spec: dict, output_path: Path) -> None:
    """Generate a multi-page DOCX document with headers, styled sections, and metadata."""
    doc = docx.Document()
    
    # Document Title
    title_p = doc.add_paragraph()
    run = title_p.add_run(doc_spec["title"])
    run.font.size = Pt(16)
    run.font.bold = True
    run.font.color.rgb = RGBColor(30, 41, 59)
    
    sub_p = doc.add_paragraph()
    sub_run = sub_p.add_run(f"RetailFlow Business Operations  |  Category: {doc_spec['category']}")
    sub_run.font.size = Pt(9)
    sub_run.font.italic = True
    sub_run.font.color.rgb = RGBColor(100, 116, 139)
    
    doc.add_paragraph()
    
    total_pages = len(doc_spec["pages"])
    for page_idx, sections in enumerate(doc_spec["pages"]):
        if page_idx > 0:
            doc.add_page_break()
            
        p_hdr = doc.add_paragraph()
        r_hdr = p_hdr.add_run(f"--- Page {page_idx + 1} of {total_pages} ---")
        r_hdr.font.size = Pt(8)
        r_hdr.font.color.rgb = RGBColor(148, 163, 184)
        
        for heading, body in sections:
            h = doc.add_heading(level=2)
            hrun = h.add_run(heading)
            hrun.font.size = Pt(12)
            hrun.font.bold = True
            hrun.font.color.rgb = RGBColor(15, 23, 42)
            
            p = doc.add_paragraph()
            prun = p.add_run(body)
            prun.font.size = Pt(10)
            prun.font.color.rgb = RGBColor(51, 65, 85)
            
    doc.save(str(output_path))


def main() -> None:
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Generating synthetic RetailFlow documents in {DOCS_DIR}...")
    
    generated_count = 0
    for doc in DOCUMENTS_SPEC:
        pdf_file = DOCS_DIR / f"{doc['filename']}.pdf"
        docx_file = DOCS_DIR / f"{doc['filename']}.docx"
        
        generate_pdf(doc, pdf_file)
        generate_docx(doc, docx_file)
        
        print(f"Generated: {pdf_file.name} ({len(doc['pages'])} pages) and {docx_file.name}")
        generated_count += 2
        
    print(f"\nSuccessfully generated {generated_count} documents ({len(DOCUMENTS_SPEC)} PDFs, {len(DOCUMENTS_SPEC)} DOCX).")


if __name__ == "__main__":
    main()
