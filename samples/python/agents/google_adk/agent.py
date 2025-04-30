import json
import random
from typing import Any, AsyncIterable, Dict, Optional, List
from google.adk.agents.llm_agent import LlmAgent
from google.adk.tools.tool_context import ToolContext
from google.adk.artifacts import InMemoryArtifactService
from google.adk.memory.in_memory_memory_service import InMemoryMemoryService
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

# Local cache for markets and businesses
markets = {}
businesses = {}
transactions = []

def create_market(name: str, description: str, operator: Dict[str, str], 
                  supported_roles: List[str]) -> dict[str, Any]:
    """
    Create a market entry.
    
    Args:
        name (str): The name of the market.
        description (str): A description of the market.
        operator (Dict[str, str]): Information about the market operator.
        supported_roles (List[str]): Roles supported in this market.
        
    Returns:
        dict[str, Any]: A dictionary containing the market data.
    """
    market_id = "market_" + str(random.randint(1000000, 9999999))
    market = {
        "market_id": market_id,
        "name": name,
        "description": description,
        "operator": operator,
        "makers": [],
        "supported_roles": supported_roles,
        "businesses": []
    }
    markets[market_id] = market
    return market

def add_business_to_market(
    market_id: str,
    business_name: str,
    description: str,
    market_roles: List[str],
    location_uri: str,
    contact_info: Optional[Dict[str, str]] = None
) -> dict[str, Any]:
    """
    Add a business to a market.
    
    Args:
        market_id (str): The ID of the market.
        business_name (str): The name of the business.
        description (str): A description of the business.
        market_roles (List[str]): Roles the business has in the market.
        location_uri (str): URI where the business agent can be found.
        contact_info (Dict[str, str], optional): Contact information.
        
    Returns:
        dict[str, Any]: A dictionary containing the business data.
    """
    if market_id not in markets:
        return {"error": "Market not found"}
    
    business_id = "business_" + str(random.randint(1000000, 9999999))
    business = {
        "business_id": business_id,
        "name": business_name,
        "description": description,
        "market_roles": market_roles,
        "location_uri": location_uri,
        "contact_info": contact_info or {}
    }
    
    businesses[business_id] = business
    markets[market_id]["businesses"].append(business_id)
    
    return business

def get_market(market_id: str) -> dict[str, Any]:
    """Get information about a specific market."""
    if market_id not in markets:
        return {"error": "Market not found"}
    
    market_info = markets[market_id].copy()
    # Remove the business IDs list from the response
    business_ids = market_info.pop("businesses", [])
    # Add full business details instead
    market_info["businesses"] = [businesses[bid] for bid in business_ids if bid in businesses]
    
    return market_info

def get_businesses_in_market(market_id: str) -> dict[str, Any]:
    """Get all businesses in a specific market."""
    if market_id not in markets:
        return {"error": "Market not found"}
    
    business_ids = markets[market_id].get("businesses", [])
    return {
        "market_id": market_id,
        "businesses": [businesses[bid] for bid in business_ids if bid in businesses]
    }

def get_businesses_by_role(market_id: str, role: str) -> dict[str, Any]:
    """Get businesses in a market with a specific role."""
    if market_id not in markets:
        return {"error": "Market not found"}
    
    business_ids = markets[market_id].get("businesses", [])
    matching_businesses = []
    
    for bid in business_ids:
        if bid in businesses and role in businesses[bid].get("market_roles", []):
            matching_businesses.append(businesses[bid])
    
    return {
        "market_id": market_id,
        "role": role,
        "businesses": matching_businesses
    }

def get_market_roles(market_id: str) -> dict[str, Any]:
    """Get the supported roles in a market."""
    if market_id not in markets:
        return {"error": "Market not found"}
    
    return {
        "market_id": market_id,
        "supported_roles": markets[market_id].get("supported_roles", [])
    }

def get_business(business_id: str) -> dict[str, Any]:
    """Get information about a specific business."""
    if business_id not in businesses:
        return {"error": "Business not found"}
    
    return businesses[business_id]

def get_all_markets() -> dict[str, Any]:
    """Get information about all available markets."""
    markets_list = []
    for market_id, market_data in markets.items():
        # Create a simplified version without the full business details
        market_info = {
            "market_id": market_id,
            "name": market_data["name"],
            "description": market_data["description"],
            "operator": market_data["operator"],
            "business_count": len(market_data.get("businesses", []))
        }
        markets_list.append(market_info)
    
    return {"markets": markets_list}

def list_products(business_id: str) -> dict[str, Any]:
    """List products or services offered by a business."""
    if business_id not in businesses:
        return {"error": "Business not found"}
    
    # Generate sample products based on the business's roles
    business = businesses[business_id]
    products = []
    
    if "manufacturer" in business["market_roles"]:
        products.extend([
            {"id": f"{business_id}_prod1", "name": "Component A", "price": 25.99, "description": "Electronic component for circuit boards"},
            {"id": f"{business_id}_prod2", "name": "Part B", "price": 15.50, "description": "Specialized part for electronics assembly"}
        ])
    
    if "seller" in business["market_roles"] or "reseller" in business["market_roles"]:
        products.extend([
            {"id": f"{business_id}_prod3", "name": "Device X", "price": 199.99, "description": "Consumer electronic device"},
            {"id": f"{business_id}_prod4", "name": "Gadget Y", "price": 49.99, "description": "Portable electronic gadget"}
        ])
    
    if "service_provider" in business["market_roles"]:
        products.extend([
            {"id": f"{business_id}_serv1", "name": "Repair Service", "price": 75.00, "description": "Electronic device repair service"},
            {"id": f"{business_id}_serv2", "name": "Maintenance Plan", "price": 120.00, "description": "Annual maintenance subscription"}
        ])
    
    if "producer" in business["market_roles"]:
        products.extend([
            {"id": f"{business_id}_prod5", "name": "Fresh Produce", "price": 12.99, "description": "Organic farm products"},
            {"id": f"{business_id}_prod6", "name": "Specialty Ingredients", "price": 24.99, "description": "Rare cooking ingredients"}
        ])
    
    if "developer" in business["market_roles"]:
        products.extend([
            {"id": f"{business_id}_prod7", "name": "Software License", "price": 299.99, "description": "Enterprise software license"},
            {"id": f"{business_id}_serv3", "name": "Custom Development", "price": 150.00, "description": "Custom software development (hourly rate)"}
        ])
    
    # Add default products if none were generated based on roles
    if not products:
        products.extend([
            {"id": f"{business_id}_gen1", "name": "Generic Product", "price": 19.99, "description": "Standard product offering"},
            {"id": f"{business_id}_gen2", "name": "Basic Service", "price": 50.00, "description": "Standard service offering"}
        ])
    
    return {
        "business_id": business_id,
        "business_name": business["name"],
        "products": products
    }

def get_product(product_id: str) -> dict[str, Any]:
    """Get detailed information about a specific product."""
    # Extract business_id from product_id (format: business_id_prodX)
    parts = product_id.split('_')
    if len(parts) < 2:
        return {"error": "Invalid product ID format"}
    
    business_id = parts[0]
    
    # Get products from the business
    business_products = list_products(business_id)
    if "error" in business_products:
        return business_products
    
    # Find the specific product
    for product in business_products["products"]:
        if product["id"] == product_id:
            return {
                "product": product,
                "business_id": business_id,
                "business_name": business_products["business_name"],
                "business_contact": businesses[business_id].get("contact_info", {})
            }
    
    return {"error": "Product not found"}

def create_transaction(
    buyer_id: str, 
    seller_id: str, 
    product_id: str, 
    quantity: int = 1
) -> dict[str, Any]:
    """Create a transaction between a buyer and seller for a product."""
    # Validate buyer and seller
    if buyer_id not in businesses:
        return {"error": "Buyer not found"}
    if seller_id not in businesses:
        return {"error": "Seller not found"}
    
    # Check if the buyer has the "buyer" role in any market
    buyer = businesses[buyer_id]
    buyer_can_buy = False
    for role in buyer["market_roles"]:
        if role in ["buyer", "retailer", "reseller", "customer"]:
            buyer_can_buy = True
            break
    
    if not buyer_can_buy:
        return {"error": "The specified business does not have a buyer role"}
    
    # Check if buyer and seller are in the same market
    shared_markets = []
    for market_id, market in markets.items():
        if buyer_id in market["businesses"] and seller_id in market["businesses"]:
            shared_markets.append(market_id)
    
    if not shared_markets:
        return {"error": "Buyer and seller are not in the same market"}
    
    # Get product details
    product_info = get_product(product_id)
    if "error" in product_info:
        return product_info
    
    # Check if the product belongs to the seller
    if product_info["business_id"] != seller_id:
        return {"error": "Product does not belong to the specified seller"}
    
    # Create transaction
    transaction_id = f"tx_{random.randint(1000000, 9999999)}"
    total_price = product_info["product"]["price"] * quantity
    
    transaction = {
        "transaction_id": transaction_id,
        "timestamp": "2025-04-30T" + f"{random.randint(10, 23)}:{random.randint(10, 59)}:{random.randint(10, 59)}Z",
        "buyer_id": buyer_id,
        "buyer_name": buyer["name"],
        "seller_id": seller_id,
        "seller_name": businesses[seller_id]["name"],
        "product_id": product_id,
        "product_name": product_info["product"]["name"],
        "quantity": quantity,
        "unit_price": product_info["product"]["price"],
        "total_price": total_price,
        "status": "completed",
        "market_id": shared_markets[0],
        "market_name": markets[shared_markets[0]]["name"]
    }
    
    transactions.append(transaction)
    
    return transaction

def get_transaction_history(business_id: str, role: str = "all") -> dict[str, Any]:
    """Get transaction history for a business, filtered by role (buyer, seller, or all)."""
    if business_id not in businesses:
        return {"error": "Business not found"}
    
    if role not in ["buyer", "seller", "all"]:
        return {"error": "Role must be 'buyer', 'seller', or 'all'"}
    
    filtered_transactions = []
    
    for tx in transactions:
        if role == "buyer" and tx["buyer_id"] == business_id:
            filtered_transactions.append(tx)
        elif role == "seller" and tx["seller_id"] == business_id:
            filtered_transactions.append(tx)
        elif role == "all" and (tx["buyer_id"] == business_id or tx["seller_id"] == business_id):
            filtered_transactions.append(tx)
    
    return {
        "business_id": business_id,
        "business_name": businesses[business_id]["name"],
        "role_filter": role,
        "transaction_count": len(filtered_transactions),
        "transactions": filtered_transactions
    }

def get_market_transaction_summary(market_id: str) -> dict[str, Any]:
    """Get a summary of transactions in a specific market."""
    if market_id not in markets:
        return {"error": "Market not found"}
    
    market_transactions = [tx for tx in transactions if tx["market_id"] == market_id]
    
    # Calculate market statistics
    total_volume = sum(tx["total_price"] for tx in market_transactions)
    transaction_count = len(market_transactions)
    
    # Get top sellers
    seller_volumes = {}
    for tx in market_transactions:
        seller_id = tx["seller_id"]
        if seller_id not in seller_volumes:
            seller_volumes[seller_id] = 0
        seller_volumes[seller_id] += tx["total_price"]
    
    top_sellers = []
    for seller_id, volume in sorted(seller_volumes.items(), key=lambda x: x[1], reverse=True)[:3]:
        top_sellers.append({
            "business_id": seller_id,
            "business_name": businesses[seller_id]["name"],
            "volume": volume
        })
    
    return {
        "market_id": market_id,
        "market_name": markets[market_id]["name"],
        "transaction_count": transaction_count,
        "total_volume": total_volume,
        "top_sellers": top_sellers,
        "recent_transactions": market_transactions[-5:] if market_transactions else []
    }


class MarketAgent:
    """An agent that handles market information and business discovery."""

    SUPPORTED_CONTENT_TYPES = ["text", "text/plain"]

    def __init__(self):
        self._agent = self._build_agent()
        self._user_id = "remote_agent"
        self._runner = Runner(
            app_name=self._agent.name,
            agent=self._agent,
            artifact_service=InMemoryArtifactService(),
            session_service=InMemorySessionService(),
            memory_service=InMemoryMemoryService(),
        )
        # Initialize a sample market and businesses for demonstration
        self._initialize_sample_data()

    def _initialize_sample_data(self):
        """Initialize sample data for demonstration purposes."""
        # Create a sample market
        electronics_market = create_market(
            name="Electronics Marketplace",
            description="A marketplace for electronic components and devices",
            operator={"name": "MarketCo", "id": "operator-1", "uri": "https://marketco.example/agent"},
            supported_roles=["seller", "buyer", "manufacturer", "reseller", "service_provider"]
        )
        
        # Add sample businesses
        add_business_to_market(
            market_id=electronics_market["market_id"],
            business_name="ComponentTech",
            description="Provider of electronic components and circuit boards",
            market_roles=["seller", "manufacturer"],
            location_uri="https://component-tech.example/agent",
            contact_info={"email": "info@component-tech.example", "phone": "+1-555-123-4567"}
        )
        
        add_business_to_market(
            market_id=electronics_market["market_id"],
            business_name="DeviceMart",
            description="Retailer of electronic devices and gadgets",
            market_roles=["seller", "reseller"],
            location_uri="https://devicemart.example/agent"
        )
        
        add_business_to_market(
            market_id=electronics_market["market_id"],
            business_name="TechRepair",
            description="Electronic device repair and maintenance services",
            market_roles=["service_provider"],
            location_uri="https://techrepair.example/agent",
            contact_info={"email": "service@techrepair.example", "phone": "+1-555-987-6543"}
        )
        
        add_business_to_market(
            market_id=electronics_market["market_id"],
            business_name="ElectronicsPro",
            description="Bulk buyer of electronics for enterprise customers",
            market_roles=["buyer"],
            location_uri="https://electronicspro.example/agent"
        )
        
        # Create another market for variety
        food_market = create_market(
            name="Gourmet Food Market",
            description="A marketplace for specialty foods and ingredients",
            operator={"name": "FoodCo", "id": "operator-2", "uri": "https://foodco.example/agent"},
            supported_roles=["producer", "distributor", "retailer", "importer"]
        )
        
        add_business_to_market(
            market_id=food_market["market_id"],
            business_name="FreshFoods",
            description="Supplier of fresh organic produce and ingredients",
            market_roles=["producer", "distributor"],
            location_uri="https://freshfoods.example/agent"
        )
        
        add_business_to_market(
            market_id=food_market["market_id"],
            business_name="GourmetGrocers",
            description="Specialty food retailer focusing on high-end culinary products",
            market_roles=["retailer"],
            location_uri="https://gourmetgrocers.example/agent",
            contact_info={"email": "sales@gourmetgrocers.example"}
        )
        
        add_business_to_market(
            market_id=food_market["market_id"],
            business_name="ImportDelights",
            description="Importer of exotic foods and spices from around the world",
            market_roles=["importer", "distributor"],
            location_uri="https://importdelights.example/agent"
        )
        
        # Create a third market to show diversity
        software_market = create_market(
            name="Software Solutions Marketplace",
            description="A marketplace for software products and services",
            operator={"name": "SoftMarket", "id": "operator-3", "uri": "https://softmarket.example/agent"},
            supported_roles=["developer", "reseller", "service_provider", "integrator", "customer"]
        )
        
        add_business_to_market(
            market_id=software_market["market_id"],
            business_name="CodeCrafters",
            description="Custom software development and solutions",
            market_roles=["developer", "service_provider"],
            location_uri="https://codecrafters.example/agent"
        )
        
        add_business_to_market(
            market_id=software_market["market_id"],
            business_name="IntegrateAll",
            description="System integration and software deployment specialists",
            market_roles=["integrator", "service_provider"],
            location_uri="https://integrateall.example/agent",
            contact_info={"email": "solutions@integrateall.example"}
        )
        
        add_business_to_market(
            market_id=software_market["market_id"],
            business_name="SoftwareSolutions",
            description="Enterprise software solution provider",
            market_roles=["developer", "reseller"],
            location_uri="https://softwaresolutions.example/agent",
            contact_info={"email": "info@softwaresolutions.example", "phone": "+1-555-444-3333"}
        )
        
        add_business_to_market(
            market_id=software_market["market_id"],
            business_name="TechCorp",
            description="Technology corporation that purchases software solutions",
            market_roles=["customer"],
            location_uri="https://techcorp.example/agent",
            contact_info={"email": "procurement@techcorp.example"}
        )
        
        # Add a few sample transactions
        create_transaction(
            buyer_id=list(filter(lambda b: "buyer" in businesses[b]["market_roles"], businesses))[0],
            seller_id=list(filter(lambda b: "seller" in businesses[b]["market_roles"], businesses))[0],
            product_id=f"{list(filter(lambda b: 'seller' in businesses[b]['market_roles'], businesses))[0]}_prod3",
            quantity=2
        )
        
        # Add another sample transaction
        create_transaction(
            buyer_id=list(filter(lambda b: "customer" in businesses[b]["market_roles"], businesses))[0],
            seller_id=list(filter(lambda b: "developer" in businesses[b]["market_roles"], businesses))[0],
            product_id=f"{list(filter(lambda b: 'developer' in businesses[b]['market_roles'], businesses))[0]}_prod7",
            quantity=5
        )

    def invoke(self, query, session_id) -> str:
        session = self._runner.session_service.get_session(
            app_name=self._agent.name, user_id=self._user_id, session_id=session_id
        )
        content = types.Content(
            role="user", parts=[types.Part.from_text(text=query)]
        )
        if session is None:
            session = self._runner.session_service.create_session(
                app_name=self._agent.name,
                user_id=self._user_id,
                state={},
                session_id=session_id,
            )
        events = list(self._runner.run(
            user_id=self._user_id, session_id=session.id, new_message=content
        ))
        if not events or not events[-1].content or not events[-1].content.parts:
            return ""
        return "\n".join([p.text for p in events[-1].content.parts if p.text])

    async def stream(self, query, session_id) -> AsyncIterable[Dict[str, Any]]:
        session = self._runner.session_service.get_session(
            app_name=self._agent.name, user_id=self._user_id, session_id=session_id
        )
        content = types.Content(
            role="user", parts=[types.Part.from_text(text=query)]
        )
        if session is None:
            session = self._runner.session_service.create_session(
                app_name=self._agent.name,
                user_id=self._user_id,
                state={},
                session_id=session_id,
            )
        async for event in self._runner.run_async(
            user_id=self._user_id, session_id=session.id, new_message=content
        ):
            if event.is_final_response():
                response = ""
                if (
                    event.content
                    and event.content.parts
                    and event.content.parts[0].text
                ):
                    response = "\n".join([p.text for p in event.content.parts if p.text])
                elif (
                    event.content
                    and event.content.parts
                    and any([True for p in event.content.parts if p.function_response])):
                    response = next((p.function_response.model_dump() for p in event.content.parts))
                yield {
                    "is_task_complete": True,
                    "content": response,
                }
            else:
                yield {
                    "is_task_complete": False,
                    "updates": "Processing the market query...",
                }

    def _build_agent(self) -> LlmAgent:
        """Builds the LLM agent for the market agent."""
        return LlmAgent(
            model="gemini-2.0-flash-001",
            name="market_agent",
            description=(
                "This agent provides information about markets and helps discover businesses"
                " within markets based on various criteria, as well as simulating transactions."
            ),
            instruction="""
            You are an agent who provides information about markets, helps discover businesses, and simulates transactions in an agent-to-agent economy.

            When you receive a query about markets or businesses:
            1. If the query is about all available markets, use get_all_markets() to retrieve a list of markets.
            2. If the query is about market information, use get_market() to retrieve details about a specific market.
            3. If the query is about all businesses in a market, use get_businesses_in_market() to retrieve all businesses.
            4. If the query is about businesses with specific roles, use get_businesses_by_role() to find relevant businesses.
            5. If the query is about the roles supported in a market, use get_market_roles() to retrieve the roles.
            6. If the query is about a specific business, use get_business() to retrieve its details.

            When you receive a transaction-related query:
            1. If the query is about available products from a business, use list_products() to show what's available.
            2. If the query is about a specific product, use get_product() to get product details.
            3. If the query is about making a purchase or transaction, use create_transaction() to complete the transaction.
            4. If the query is about transaction history, use get_transaction_history() to show past transactions.
            5. If the query is about market transaction activity, use get_market_transaction_summary() to show market statistics.

            For any query, identify what the user is looking for and use the appropriate function to retrieve the information.
            Provide a helpful, concise response that directly addresses their query.
            
            When referencing a business's location, always refer to it as the business's "agent location" or "agent URI".
            """,
            tools=[
                create_market,
                add_business_to_market,
                get_market,
                get_all_markets,
                get_businesses_in_market,
                get_businesses_by_role,
                get_market_roles,
                get_business,
                list_products,
                get_product,
                create_transaction,
                get_transaction_history,
                get_market_transaction_summary,
            ],
        )