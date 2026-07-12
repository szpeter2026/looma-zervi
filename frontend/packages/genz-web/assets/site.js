(function () {
  var cfg = window.GENZ_SITE || {};

  function qs(sel) {
    return document.querySelector(sel);
  }

  function qsa(sel) {
    return Array.prototype.slice.call(document.querySelectorAll(sel));
  }

  function setActiveNav() {
    var path = window.location.pathname.replace(/\.html$/, "") || "/";
    qsa("[data-nav]").forEach(function (link) {
      var href = link.getAttribute("href") || "";
      var normalized = href.replace(/\.html$/, "");
      if (path === normalized || (path === "/" && normalized === "/index")) {
        link.classList.add("active");
      }
    });
  }

  function injectLegalEntity() {
    var name = cfg.legalEntityName || "[Legal entity name pending]";
    qsa("[data-legal-entity]").forEach(function (el) {
      el.textContent = name;
    });
  }

  function injectSupportEmail() {
    var email = cfg.supportEmail || "zervi@genz.ltd";
    qsa("[data-support-email]").forEach(function (el) {
      if (el.tagName === "A") {
        el.href = "mailto:" + email;
        el.textContent = email;
      } else {
        el.textContent = email;
      }
    });
  }

  function injectFooter() {
    var footer = qs("[data-site-footer]");
    if (!footer) return;

    var entity = cfg.legalEntityName || "[Legal entity name pending]";
    var year = new Date().getFullYear();
    footer.innerHTML =
      '<div class="footer-grid">' +
      '<div>' +
      "<strong>" + (cfg.brandName || "GenZ") + " · " + (cfg.productName || "PlanetX") + "</strong><br>" +
      (cfg.tagline || "AI Career Growth Partner") +
      "<p>© " + year + " " + entity + ". All rights reserved.</p>" +
      "</div>" +
      '<div class="footer-links">' +
      '<a href="/pricing.html">Pricing</a>' +
      '<a href="/legal/privacy.html">Privacy</a>' +
      '<a href="/legal/terms.html">Terms</a>' +
      '<a href="/legal/refund.html">Refund &amp; Cancellation</a>' +
      '<a data-support-email href="mailto:' + (cfg.supportEmail || "zervi@genz.ltd") + '">' +
      (cfg.supportEmail || "zervi@genz.ltd") +
      "</a>" +
      "</div>" +
      "</div>";
  }

  var FALLBACK_PLANS = [
    {
      tier: "free",
      name: "Free",
      price_monthly: 0,
      currency: "USD",
      features: [
        "30 AI chats per day",
        "Basic job matching",
        "3 resume parses per day",
      ],
      upgradable: false,
    },
    {
      tier: "supporter",
      name: "Supporter",
      price_monthly: 1.99,
      currency: "USD",
      features: [
        "100 AI chats per day",
        "Advanced job matching",
        "Unlimited resume parsing",
        "PlanetX supporter badge",
      ],
      upgradable: true,
    },
    {
      tier: "pro",
      name: "Pro",
      price_monthly: 5.99,
      currency: "USD",
      features: [
        "Unlimited AI chats",
        "Full job matching",
        "Unlimited resume parsing",
        "Advanced analytics",
        "Priority support",
      ],
      upgradable: true,
    },
  ];

  function formatPrice(plan) {
    if (!plan.price_monthly) return "$0";
    return "$" + plan.price_monthly;
  }

  function waitlistMailto(planName) {
    return (
      "mailto:" +
      (cfg.supportEmail || "zervi@genz.ltd") +
      "?subject=" +
      encodeURIComponent("PlanetX waitlist — " + planName)
    );
  }

  function renderPricingCard(plan, popular) {
    var card = document.createElement("article");
    card.className = "card" + (popular ? " popular" : "");
    var cta =
      plan.tier === "free"
        ? '<a class="btn btn-secondary" href="' +
          waitlistMailto("Free") +
          '">Get started free</a>'
        : '<a class="btn btn-primary" href="' +
          waitlistMailto(plan.name) +
          '">Join waitlist</a>';

    card.innerHTML =
      (popular ? '<div class="badge">Most popular</div>' : "") +
      "<h3>" +
      plan.name +
      "</h3>" +
      '<div class="price">' +
      formatPrice(plan) +
      '<span> / month</span></div>' +
      "<p>Billed monthly in USD. Digital SaaS subscription.</p>" +
      "<ul>" +
      plan.features.map(function (f) {
        return "<li>" + f + "</li>";
      }).join("") +
      "</ul>" +
      '<div style="margin-top:1rem;">' +
      cta +
      "</div>";
    return card;
  }

  function loadPricing() {
    var grid = qs("#pricing-grid");
    var status = qs("#pricing-status");
    if (!grid) return;

    function paint(plans, source) {
      grid.innerHTML = "";
      plans.forEach(function (plan) {
        grid.appendChild(renderPricingCard(plan, plan.tier === "pro"));
      });
      if (status) {
        status.textContent =
          source === "api"
            ? "Live pricing loaded from Looma API (region=US)."
            : "Pricing shown from contract fallback (API unavailable).";
        status.className = "pricing-status " + (source === "api" ? "ok" : "");
      }
    }

    var apiBase = cfg.apiBase || "https://api.genz.ltd";
    fetch(apiBase + "/v1/payment/plans?region=US")
      .then(function (res) {
        if (!res.ok) throw new Error("plans unavailable");
        return res.json();
      })
      .then(function (data) {
        var plans = (data.plans || []).filter(function (p) {
          return p.tier !== "enterprise";
        });
        if (!plans.length) throw new Error("empty plans");
        paint(plans, "api");
      })
      .catch(function () {
        paint(FALLBACK_PLANS, "fallback");
      });
  }

  document.addEventListener("DOMContentLoaded", function () {
    setActiveNav();
    injectLegalEntity();
    injectSupportEmail();
    injectFooter();
    loadPricing();
  });
})();
