import json
import os

from dotenv import load_dotenv
from openai import OpenAI

from product_search import (
    get_product_details,
    check_product_availability,
    compare_products,
)

from hybrid_search import hybrid_search_products


load_dotenv()

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
)

MODEL = "nvidia/nemotron-3-ultra-550b-a55b:free"


tools = [
    {
        "type": "function",
        "function": {
            "name": "search_products",
            "description": (
                "Search the laptop catalog using hard product requirements. "
                "Use this to find products matching price, RAM, GPU, SSD, "
                "brand, or operating system requirements."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "max_price": {
                        "type": "number",
                        "description": "Maximum price in USD.",
                    },
                    "min_ram": {
                        "type": "integer",
                        "description": "Minimum RAM in GB.",
                    },
                    "gpu_brand": {
                        "type": "string",
                        "description": "GPU brand such as NVIDIA, AMD, or Intel.",
                    },
                    "min_ssd": {
                        "type": "integer",
                        "description": "Minimum SSD capacity in GB.",
                    },
                    "brand": {
                        "type": "string",
                        "description": "Laptop brand.",
                    },
                    "os": {
                        "type": "string",
                        "description": "Operating system.",
                    },
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_product_details",
            "description": "Get complete specifications for a specific laptop.",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_id": {
                        "type": "string",
                        "description": "Product ID such as LAP3706.",
                    }
                },
                "required": ["product_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "compare_products",
            "description": "Compare specifications of multiple laptops.",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_ids": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of product IDs to compare.",
                    }
                },
                "required": ["product_ids"],
            },
        },
    },
]


messages = [
    {
        "role": "system",
        "content": """
            You are an AI shopping agent for a laptop store.

            Use the available tools to find laptops matching the user's requirements,
            verify their availability, and explain the results.

            Rules:

                1. Never invent product-specific facts such as specifications, prices,
                    stock quantities, availability, or delivery times.

                2. Tool results are the source of truth for all product-specific facts.

                3. Do not add general technical explanations about hardware
                capabilities, performance, compatibility, ML suitability, or expected
                workloads. Keep the answer grounded in the verified catalog data.

                4. Do not infer unverified properties of a specific product.

                5. Recommendations must be based on the user's requirements and verified
                    product information.

                6. Availability is already verified by the Python inventory workflow
                before the results are returned to you. Do not perform, simulate, or
                repeat inventory checks yourself.

                7. A positive store quantity means only that the product is currently
                recorded in that store's inventory.

                8. Store inventory does not confirm immediate pickup, reservation,
                order readiness, or a guaranteed pickup time.

                9. Never say "ready for pickup", "immediate pickup", "available for
                pickup", "ready to order", or similar unless a tool explicitly
                confirms it.

                10. Never infer delivery time or delivery date from stock quantity.

                11. Clearly distinguish:
                    - product recorded in store inventory
                    - product recorded in warehouse inventory
                    - estimated warehouse-to-store transfer time

                12. Warehouse transfer estimates refer only to the transfer from the
                    warehouse to the destination store. They are NOT customer delivery
                    estimates.

                13. If the user specifies a delivery deadline, compare it only with
                    the available warehouse-to-store transfer estimate. Do not claim that
                    the product will arrive to the customer within that deadline unless
                    customer delivery information is explicitly provided.

                14. When presenting recommendations, include relevant verified
                    specifications, price, and availability information.

                15. Only recommend products from the verified_products returned by
                    search_products.

                16. Do not mention availability, stock, or delivery information for
                    products that are not present in verified_products.

                17. Use precise availability wording:
                    - store_stock: "recorded in store inventory"
                    - warehouse_delivery: "in warehouse stock; estimated transfer to
                    [store] is X–Y days"

                18. Do not rank products as "best", "best value", "winner", or similar.
                    Compare verified specifications and explain trade-offs relevant to the
                    user's requirements.

                19. Only state product-specific technical specifications that appear
                    explicitly in the tool results.

                20. Do not derive product-specific technical facts from model names,
                    hardware names, or general technical knowledge.

                21. General technical knowledge may be used only to explain the general
                    meaning of a verified specification, without making additional claims
                    about the specific product.

                22. Do not claim that a specific product or component is newer, faster,
                    better, more powerful, more suitable, or technically superior unless
                    the relevant comparison is explicitly supported by tool results.

                23. Do not infer GPU architecture, Tensor Cores, CUDA capabilities,
                    benchmark performance, upgradeability, soldered RAM, thermal
                    performance, or other hardware characteristics unless explicitly
                    provided by a tool result.

                24. Do not call compare_products unless the user explicitly asks for a
                    detailed comparison of specific products.

                25. Do not call search_products again with the same arguments unless
                    the user changes or adds requirements.

                26. The verified_products returned by search_products are the only
                    products that may be recommended in the current response.

                27. Never invent missing product information. If a required fact is
                    not present in the tool results, state that it is not available.

                28. Never use phrases such as "immediate availability",
                    "immediately available", "available within X days", "will arrive
                    within X days", or "meets the delivery deadline" unless the tool
                    results explicitly provide customer delivery information supporting
                    that claim.

                29. Never infer how quickly a customer can obtain a product from store
                    inventory. Store inventory only means that the product is recorded in
                    that store's inventory.

                30. Never use phrases such as "same day", "today", "immediately",
                    "available now", or "obtainable within X days" unless customer
                    fulfillment or delivery information is explicitly provided by a tool.

                31. If the user specifies a delivery deadline but the tools provide only
                    warehouse-to-store transfer information, explicitly state that customer
                    delivery time cannot be verified from the available data.

                32. Do not compare specific GPUs, CPUs, RAM configurations, or other
                    hardware components using facts that are not explicitly present in the
                    tool results. This includes generation, architecture, age, performance,
                    power, compatibility, features, and capabilities.

                33. Do not infer CUDA support, Tensor Cores, GPU architecture,
                    generation superiority, benchmark performance, or ML performance from
                    the GPU model name.

                34. ram_max_gb is only a catalog field representing the maximum RAM
                    capacity recorded for the product. Do not describe it as upgradeable,
                    replaceable, supported, expandable, limited, or physically configurable.
                    You may only state the recorded value itself, for example:
                    "RAM: 16 GB; catalog maximum: 32 GB."

                35. Keep the final answer focused and concise. Do not add separate
                    sections that repeat information already shown in the product list.
                    Do not add "Recorded Specifications", "Technical Summary",
                    "Availability Notes", or similar repetitive sections. Include relevant
                    availability limitations directly in the product entries or in one
                    short final note.

                36. Keep the final answer focused on the user's stated requirements,
                    verified product specifications, verified inventory status, and
                    verified transfer information.

                37. Do not describe one product component as newer, older, higher-generation,
                    lower-generation, or from a different generation than another component
                    unless this comparison is explicitly provided by a tool result.

                38. Never state that a specific GPU supports CUDA, Tensor Cores,
                    CUDA cores, or any other GPU-specific capability unless that capability
                    is explicitly present in the tool results.

                39. The presence of an NVIDIA GPU alone must not be treated as evidence
                    for any specific GPU capability in the final answer.

                40. Do not use general knowledge about a GPU model to add technical
                    specifications or capabilities to a product recommendation.

                41. Do not compare GPU or CPU models using external or general
                    knowledge. Do not describe one component as newer, older, faster,
                    slower, stronger, weaker, better, worse, more capable, less capable,
                    higher-generation, or lower-generation unless the tool results
                    explicitly provide that comparison.

                42. The Python availability workflow checks all candidates returned by
                    the product search before verified_products and verified_count are
                    created. Therefore, verified_count represents the total number of
                    products that passed the availability check among the searched
                    candidates. Do not claim that this is the total number of matching
                    products in the entire catalog.

                43. If the user specifies a deadline, do not say that a product meets
                    the deadline unless the tool results explicitly verify the complete
                    customer fulfillment timeline. Store stock and warehouse-to-store
                    transfer time alone do not verify the customer's deadline.

                44. The verified_count field is the authoritative total number of
                    verified products. When verified_count is greater than 8, present only
                    the products included in verified_products, but clearly state that
                    verified_products contains only a displayed subset of the total
                    verified_count. Do not reconstruct, infer, or list additional products
                    that are not present in verified_products. Do not claim that the
                    displayed products are objectively better or superior to products that
                    are not displayed.

                45. Never calculate or invent the total number of verified products from
                    the displayed product list. Use verified_count exactly as provided by
                    the tool result.

                46. Do not omit, duplicate, merge, or invent product identities within
                    the displayed verified_products. Each displayed product must correspond
                    to exactly one product object returned by the tool.

                47. When verified_count is greater than the number of products in
                    verified_products, explicitly distinguish the total verified count from
                    the number of products displayed. For example, if verified_count is 20
                    and 8 products are displayed, say "I found 20 verified products and am
                    showing 8 of them." Never say or imply that only 8 products were
                    verified.

                48. Do not repeat the same product specifications, availability data,
                    or technical facts in a separate summary after the product list. Each
                    fact should normally be presented once.

                49. When the user gives a delivery or availability deadline but does not
                    specify a destination store, do not conclude that any product meets,
                    fits, may fit, or is likely to meet the deadline. Warehouse-to-store
                    transfer times may be reported for each destination store exactly as
                    provided by the tool, but they must not be converted into a customer
                    delivery, pickup, or fulfillment estimate.

                50. When destination_store is not specified, do not ask the user to
                    choose a pickup store unless the user explicitly asks for pickup or
                    store selection. Simply report the available store inventory and/or
                    warehouse-to-store transfer information returned by the tool.

                51. Never summarize availability for verified_count products using only
                    the displayed verified_products subset. If only 8 products are present
                    in verified_products, availability statements must refer only to those
                    8 products. The remaining verified products must not be assigned store,
                    warehouse, quantity, or transfer information unless those objects are
                    explicitly present in the tool result provided to the model.

                52. When multiple destination stores are present in an availability
                    object, keep their transfer estimates separate. Do not combine them
                    into a single range such as "1–3 days" or otherwise merge different
                    destination routes.

                53. Do not add a follow-up question, offer, or suggestion at the end of
                    the answer unless the user explicitly asks for further assistance.

                54. Never combine, summarize, compress, or derive a single transfer
                    range from multiple destination routes. This prohibition applies
                    everywhere in the final answer, including headings, introductions,
                    notes, conclusions, and deadline explanations. If the tool result
                    contains 1–2 days for Astana Mega Silk Way and 2–3 days for Astana
                    Khan Shatyr, the final answer must contain exactly those two separate
                    route estimates and must never contain "1–3 days".

                55. When no destination store is specified, do not ask, suggest, offer,
                    or invite the user to choose a store, pickup location, or delivery
                    option. Do not end the answer with such an offer. Simply report the
                    verified availability and the separate transfer routes provided by the
                    tool result.

                56. Do not restate the user's deadline as a separate "important note"
                    unless necessary to explain a limitation. If a deadline is mentioned,
                    state only that customer fulfillment time cannot be verified from the
                    available data because the tool provides warehouse-to-store transfer
                    times only. Never compare, combine, or interpret transfer times against
                    the customer's deadline.

                57. When verified_count is 0, state only that no matching products
                    were found in the available catalog or inventory. Do not claim
                    that such a product does not exist in the real world, does not
                    exist generally, or cannot be found elsewhere.
        """
    },
    {
        "role": "user",
        "content": (
            "I need a Lenovo laptop with 128 GB RAM and 20 TB SSD under $100."
        ),
    },
]


def detect_destination_store(user_query):
    query = user_query.lower()

    if "mega silk way" in query or "мега силк вей" in query:
        return "Astana Mega Silk Way"

    if "khan shatyr" in query or "хан шатыр" in query:
        return "Astana Khan Shatyr"

    return None


def execute_tool(tool_call, user_query):
    function_name = tool_call.function.name
    arguments = json.loads(tool_call.function.arguments)

    print(f"\nTOOL: {function_name}")
    print(f"ARGS: {arguments}")

    if function_name == "search_products":
        return hybrid_search_products(
            user_query,
            top_k=1000,
        )

    if function_name == "get_product_details":
        return get_product_details(**arguments)

    if function_name == "compare_products":
        return compare_products(**arguments)

    return {"error": f"Unknown tool: {function_name}"}


FORBIDDEN_CLAIMS = [
    # Unsupported GPU / ML claims
    "cuda",
    "tensor core",
    "cuda core",
    "entry-level",
    "more capable",
    "less capable",
    "more powerful",
    "less powerful",
    "higher performance",
    "lower performance",
    "better performance",
    "faster",
    "slower",

    # Unsupported hardware comparisons
    "newer",
    "older",
    "higher-generation",
    "lower-generation",
    "higher generation",
    "lower generation",
    "more advanced",
    "less advanced",
    "superior",
    "inferior",

    # Unsupported RAM / hardware configuration claims
    "upgradeable",
    "upgradable",
    "soldered",
    "replaceable",
    "fixed at",
    "limited to",
    "supports up to",

    # Unsupported availability claims
    "same day",
    "immediately",
    "available now",
    "ready for pickup",
    "immediate pickup",
    "ready to order",
    "available for pickup",
    "obtainable within",
    "will arrive within",
    "meets the delivery deadline",

    # Unsupported performance / suitability claims
    "suitable for",
    "ideal for",
    "good for",
    "great for",
    "enough for",
    "handles",
    "can run",
    "can train",

    "better for",
    "best for",
    "worse for",
    "newer architecture",
    "older architecture",
    "newer cpu",
    "older cpu",
    "newer gpu",
    "older gpu",
    "more suitable",
    "less suitable",
    "expandability",
    "expandable",
]


def has_ungrounded_claim(text):
    text_lower = text.lower()

    return any(
        claim in text_lower
        for claim in FORBIDDEN_CLAIMS
    )


search_called = False
search_result_cache = None

user_query = messages[-1]["content"]

while True:

    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        tools=tools,
    )

    if not response.choices:
        print("ERROR: OpenRouter returned no choices.")
        print(response)
        break

    message = response.choices[0].message

    if not message.tool_calls:

        final_answer = message.content

        if has_ungrounded_claim(final_answer):

            messages.append(message)

            messages.append({
                "role": "user",
                "content": (
                    "Rewrite your previous answer using ONLY information "
                    "explicitly present in the tool results. Remove all "
                    "unsupported technical claims and unsupported availability "
                    "claims. Do not add any new information. "
                    "Return only the corrected answer."
                ),
            })

            retry_response = client.chat.completions.create(
                model=MODEL,
                messages=messages,
                tools=tools,
            )

            if retry_response.choices:
                final_answer = retry_response.choices[0].message.content

        print(final_answer)
        break

    messages.append(message)

    for tool_call in message.tool_calls:

        result = execute_tool(
            tool_call,
            user_query,
        )

        if tool_call.function.name == "search_products":

            if search_called:
                result = search_result_cache

            else:
                search_called = True

                verified_products = []

                for product in result:
                    destination_store = detect_destination_store(user_query)

                    availability = check_product_availability(
                        product_id=product["product_id"],
                        destination_store=destination_store,
                    )

                    if availability["status"] in {
                        "store_stock",
                        "warehouse_delivery",
                    }:
                        verified_products.append({
                            "product": product,
                            "availability": availability,
                        })

                all_verified_products = verified_products

                result = {
                    "verified_products": all_verified_products[:8],
                    "verified_count": len(all_verified_products),
                    "checked_candidates": len(result),
                }

                search_result_cache = result

        print(f"\nRESULT: {result}")

        messages.append({
            "role": "tool",
            "tool_call_id": tool_call.id,
            "content": json.dumps(result, default=str),
        })