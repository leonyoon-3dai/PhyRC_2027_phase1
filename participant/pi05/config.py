"""Use JAX LoRA for both language and action expert; shared train/infer transforms."""
from openpi.models.pi0_config import Pi0Config
from openpi import transforms


def model_config():
    return Pi0Config(pi05=True,action_horizon=10,paligemma_variant='gemma_2b_lora',
                     action_expert_variant='gemma_300m_lora')


def model_transforms():
    from openpi.models.tokenizer import PaligemmaTokenizer
    return transforms.Group(inputs=[transforms.ResizeImages(224,224),
                    transforms.TokenizePrompt(PaligemmaTokenizer(200),discrete_state_input=True),
                    transforms.PadStatesAndActions(32)])


def train_config(base,checkpoint_dir,steps,batch_size,resume=False):
    from openpi.training.config import TrainConfig
    from openpi.training.weight_loaders import CheckpointWeightLoader
    model = model_config()
    return TrainConfig(name='phyrc_pi05_lora',exp_name='pipeline',model=model,
        freeze_filter=model.get_freeze_filter(),weight_loader=CheckpointWeightLoader(str(base)),
        batch_size=batch_size,num_train_steps=steps,num_workers=0,ema_decay=None,
        wandb_enabled=False,checkpoint_base_dir=str(checkpoint_dir),
        log_interval=1,save_interval=10,keep_period=10,resume=resume)
