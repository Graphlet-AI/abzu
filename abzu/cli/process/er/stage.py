"""Entity resolution stage command to run block, match, and eval consecutively."""

import click

from abzu.config import config


@click.command(context_settings={"show_default": True})
@click.option(
    "--iteration",
    "-i",
    type=int,
    default=config.get("er.iteration", 1),
    help="Iteration number for entity resolution",
)
@click.option(
    "--block-size",
    "-m",
    type=int,
    default=config.get("er.max_block_size", 50),
    help="Maximum block size for entity resolution blocking",
)
@click.option(
    "--batch-concurrency",
    "-b",
    type=int,
    default=config.get("er.batch_concurrency", 10),
    help="Number of concurrent batches for matching",
)
@click.option(
    "--local-mode",
    is_flag=True,
    help="Run Spark in local mode",
)
@click.pass_context
def stage(ctx, iteration, block_size, batch_concurrency, local_mode):
    """Run complete entity resolution stage: block, match, and eval."""
    from abzu.logs import get_logger

    logger = get_logger(__name__)

    logger.info(f"Starting entity resolution stage for iteration {iteration}")
    logger.info(f"Parameters: block_size={block_size}, batch_concurrency={batch_concurrency}")

    # Import the commands we need to run
    from abzu.cli.process.er.block.names import names as block_names
    from abzu.cli.process.er.eval.names import names as eval_names
    from abzu.cli.process.er.match.names import names as match_names

    try:
        # Step 1: Run blocking
        logger.info(f"Step 1/3: Running blocking for iteration {iteration}")
        ctx.invoke(
            block_names,
            iteration=iteration,
            max_block_size=block_size,
            local_mode=local_mode,
        )
        logger.info("Blocking completed successfully")

        # Step 2: Run matching
        logger.info(f"Step 2/3: Running matching for iteration {iteration}")
        ctx.invoke(
            match_names,
            iteration=iteration,
            batch_concurrency=batch_concurrency,
            local_mode=local_mode,
        )
        logger.info("Matching completed successfully")

        # Step 3: Run evaluation
        logger.info(f"Step 3/3: Running evaluation for iteration {iteration}")
        ctx.invoke(
            eval_names,
            iteration=iteration,
            local_mode=local_mode,
        )
        logger.info("Evaluation completed successfully")

        logger.info(f"Entity resolution stage completed successfully for iteration {iteration}")

    except Exception as e:
        logger.error(f"Entity resolution stage failed: {e}")
        raise click.ClickException(f"Stage failed: {e}")
