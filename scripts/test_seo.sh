#!/bin/bash
# SEO Testing Script - Test all fixes after deployment

echo "🔍 Testing SEO Fixes for iamhemanth.in"
echo "========================================"
echo ""

SITE_URL="https://iamhemanth.in"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test 404 responses
echo "1. Testing 404 Status Codes..."
echo "--------------------------------"

test_404() {
    local url=$1
    local status=$(curl -s -o /dev/null -w "%{http_code}" "$url")
    if [ "$status" == "404" ]; then
        echo -e "${GREEN}✓${NC} $url returns 404"
    else
        echo -e "${RED}✗${NC} $url returns $status (expected 404)"
    fi
}

test_404 "$SITE_URL/blog/non-existent-post"
test_404 "$SITE_URL/projects/non-existent-project"
test_404 "$SITE_URL/blog/tag/non-existent-tag"
test_404 "$SITE_URL/blog/category/non-existent-category"
echo ""

# Test sitemap
echo "2. Testing Sitemap..."
echo "--------------------------------"
sitemap_status=$(curl -s -o /dev/null -w "%{http_code}" "$SITE_URL/sitemap.xml")
if [ "$sitemap_status" == "200" ]; then
    echo -e "${GREEN}✓${NC} Sitemap accessible"
    
    # Check if sitemap has lastmod dates
    lastmod_count=$(curl -s "$SITE_URL/sitemap.xml" | grep -c "<lastmod>")
    if [ "$lastmod_count" -gt 0 ]; then
        echo -e "${GREEN}✓${NC} Sitemap contains $lastmod_count lastmod dates"
    else
        echo -e "${RED}✗${NC} Sitemap missing lastmod dates"
    fi
else
    echo -e "${RED}✗${NC} Sitemap returns $sitemap_status (expected 200)"
fi
echo ""

# Test robots.txt
echo "3. Testing robots.txt..."
echo "--------------------------------"
robots_status=$(curl -s -o /dev/null -w "%{http_code}" "$SITE_URL/robots.txt")
if [ "$robots_status" == "200" ]; then
    echo -e "${GREEN}✓${NC} robots.txt accessible"
    
    # Check if robots.txt contains sitemap reference
    if curl -s "$SITE_URL/robots.txt" | grep -q "Sitemap:"; then
        echo -e "${GREEN}✓${NC} robots.txt contains sitemap reference"
    else
        echo -e "${RED}✗${NC} robots.txt missing sitemap reference"
    fi
else
    echo -e "${RED}✗${NC} robots.txt returns $robots_status (expected 200)"
fi
echo ""

# Test security headers
echo "4. Testing Security Headers..."
echo "--------------------------------"
headers=$(curl -s -I "$SITE_URL")

check_header() {
    local header=$1
    if echo "$headers" | grep -qi "$header"; then
        echo -e "${GREEN}✓${NC} $header present"
    else
        echo -e "${YELLOW}⚠${NC} $header missing"
    fi
}

check_header "X-Content-Type-Options"
check_header "X-Frame-Options"
check_header "X-XSS-Protection"
check_header "Referrer-Policy"
echo ""

# Test meta tags on homepage
echo "5. Testing Meta Tags (Homepage)..."
echo "--------------------------------"
homepage=$(curl -s "$SITE_URL")

check_meta() {
    local meta=$1
    if echo "$homepage" | grep -qi "$meta"; then
        echo -e "${GREEN}✓${NC} $meta present"
    else
        echo -e "${RED}✗${NC} $meta missing"
    fi
}

check_meta "meta name=\"description\""
check_meta "meta name=\"robots\""
check_meta "link rel=\"canonical\""
check_meta "property=\"og:title\""
check_meta "application/ld+json"
echo ""

# Test humans.txt
echo "6. Testing humans.txt..."
echo "--------------------------------"
humans_status=$(curl -s -o /dev/null -w "%{http_code}" "$SITE_URL/humans.txt")
if [ "$humans_status" == "200" ]; then
    echo -e "${GREEN}✓${NC} humans.txt accessible"
else
    echo -e "${YELLOW}⚠${NC} humans.txt returns $humans_status"
fi
echo ""

# Summary
echo "========================================"
echo "✅ SEO Testing Complete!"
echo ""
echo "Next Steps:"
echo "1. Fix any failed tests above"
echo "2. Use Google's Rich Results Test: https://search.google.com/test/rich-results"
echo "3. Validate sitemap in Google Search Console"
echo "4. Request re-indexing for affected pages"
echo "5. Monitor coverage report for 1-2 weeks"
echo ""
echo "Useful Tools:"
echo "- Google Search Console: https://search.google.com/search-console"
echo "- Rich Results Test: https://search.google.com/test/rich-results"
echo "- PageSpeed Insights: https://pagespeed.web.dev/"
echo "- W3C Validator: https://validator.w3.org/"
