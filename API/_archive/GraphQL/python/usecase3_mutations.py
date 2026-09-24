import strawberry
import asyncio

@strawberry.type
class User:
    id: str
    name: str

@strawberry.type
class Query:
    @strawberry.field
    def dummy(self) -> str:
        return "GraphQL requires at least one query"

@strawberry.type
class Mutation:
    @strawberry.mutation
    def create_user(self, name: str) -> User:
        # Simulated DB Insert
        print(f"Inserting {name} into database...")
        return User(id="generated_uuid_123", name=name)

schema = strawberry.Schema(query=Query, mutation=Mutation)

async def run_mutation():
    mutation = """
        mutation {
            createUser(name: "Bob") {
                id
                name
            }
        }
    """
    result = await schema.execute(mutation)
    print("Mutation Result:", result.data)

if __name__ == "__main__":
    asyncio.run(run_mutation())
